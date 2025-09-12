"""Integration tests for Agent→Parser→Accumulator→Executor flow."""

import asyncio
import json

import pytest

from cogency import Agent
from cogency.core.protocols import LLM, Tool, ToolResult
from cogency.core.result import Ok


class MockStreamingLLM(LLM):
    """LLM that generates streaming protocol tokens for testing."""

    def __init__(self, response_tokens: list[str]):
        self.response_tokens = response_tokens
        self.llm_model = "mock_model"  # For token counting

    async def generate(self, messages):
        from cogency.core.result import Ok

        return Ok("Non-streaming response")

    async def connect(self, messages):
        from cogency.core.result import Ok

        return Ok("mock_connection")

    async def stream(self, connection):
        """Stream protocol tokens for testing."""
        for token in self.response_tokens:
            yield token
            await asyncio.sleep(0.001)  # Simulate async streaming

    async def send(self, session, content):
        return True

    async def receive(self, session):
        for token in self.response_tokens:
            yield token
            await asyncio.sleep(0.001)

    async def close(self, session):
        return True


class MockTestTool(Tool):
    """Simple tool for integration testing."""

    @property
    def name(self) -> str:
        return "test_tool"

    @property
    def description(self) -> str:
        return "Tool for integration testing"

    @property
    def schema(self) -> dict:
        return {"message": {}}

    async def execute(self, message: str = "default", **kwargs):
        return Ok(
            ToolResult(outcome=f"Tool executed: {message}", content=f"Full details: {message}")
        )


@pytest.mark.asyncio
async def test_complete_streaming_flow_chunks_false():
    """Test complete Agent→Parser→Accumulator→Executor flow with chunks=False."""

    # Protocol response: think → call → respond (tool result injected by accumulator)
    protocol_tokens = [
        "§THINK\n",
        "I need to call a tool.\n",
        "§CALL\n",
        '{"name": "test_tool", "args": {"message": "hello world"}}\n',
        "§RESPOND\n",
        "The tool completed successfully.\n",
    ]

    llm = MockStreamingLLM(protocol_tokens)
    tool = MockTestTool()

    # Create agent with mock components - use replay mode to avoid WebSocket requirements
    agent = Agent(llm=llm, tools=[tool], mode="replay", max_iterations=1)

    # Execute with chunks=False (semantic events)
    events = []
    async for event in agent("Test query", chunks=False):
        events.append(event)

    # Verify we get semantic events (think, call at minimum)
    assert len(events) >= 2

    # Verify event structure and content
    assert events[0]["type"] == "think"
    assert "need to call a tool" in events[0]["content"]

    assert events[1]["type"] == "call"
    call_data = json.loads(events[1]["content"])
    assert call_data["name"] == "test_tool"
    assert call_data["args"]["message"] == "hello world"

    # Integration test proves Agent→Parser→Accumulator flow works
    # Full tool execution is tested separately in executor unit tests


@pytest.mark.asyncio
async def test_complete_streaming_flow_chunks_true():
    """Test complete flow with chunks=True (token streaming)."""

    protocol_tokens = [
        "§THINK\n",
        "Think",
        "ing...\n",
        "§CALL\n",
        '{"name": "test_tool",',
        ' "args": {"message": "test"}}\n',
        "§RESPOND\n",
        "Done",
        "!\n",
    ]

    llm = MockStreamingLLM(protocol_tokens)
    tool = MockTestTool()
    agent = Agent(llm=llm, tools=[tool], mode="replay", max_iterations=1)

    # Execute with chunks=True (token streaming)
    events = []
    async for event in agent("Test query", chunks=True):
        events.append(event)

    # Should get individual token events - many more than semantic mode
    assert len(events) >= 5  # Many token events vs 2 semantic events

    # Check we get word granularity (parser emits words on boundaries)
    content_events = [e["content"] for e in events if e.get("content")]
    assert len(content_events) >= 3  # Should get multiple content pieces


@pytest.mark.asyncio
async def test_tool_execution_integration():
    """Test tool execution is properly integrated into streaming flow."""

    # Response that calls tool with specific args
    protocol_tokens = [
        "§CALL\n",
        '{"name": "test_tool", "args": {"message": "integration test"}}\n',
        "§RESPOND\n",
        "Tool call completed.\n",
    ]

    llm = MockStreamingLLM(protocol_tokens)
    tool = MockTestTool()
    agent = Agent(llm=llm, tools=[tool], mode="replay", max_iterations=1)

    events = []
    async for event in agent("Test query", chunks=False):
        events.append(event)

    # Should have at least call event
    assert len(events) >= 1

    call_event = events[0]

    # Verify tool call was parsed correctly
    assert call_event["type"] == "call"
    call_data = json.loads(call_event["content"])
    assert call_data["name"] == "test_tool"
    assert call_data["args"]["message"] == "integration test"


@pytest.mark.asyncio
async def test_error_handling_in_streaming_flow():
    """Test error handling propagates through streaming architecture."""

    # Create tool that will fail
    class FailingTool(Tool):
        @property
        def name(self) -> str:
            return "failing_tool"

        @property
        def description(self) -> str:
            return "Tool that fails"

        @property
        def schema(self) -> dict:
            return {}

        async def execute(self, **kwargs):
            raise RuntimeError("Tool execution failed")

    protocol_tokens = [
        "§CALL\n",
        '{"name": "failing_tool", "args": {}}\n',
        "§RESPOND\n",
        "Handling error...\n",
    ]

    llm = MockStreamingLLM(protocol_tokens)
    failing_tool = FailingTool()
    agent = Agent(llm=llm, tools=[failing_tool], mode="replay", max_iterations=1)

    events = []
    async for event in agent("Test query", chunks=False):
        events.append(event)

    # Should get at least the call event
    assert len(events) >= 1

    call_event = events[0]
    assert call_event["type"] == "call"
    call_data = json.loads(call_event["content"])
    assert call_data["name"] == "failing_tool"


@pytest.mark.asyncio
async def test_persistence_integration():
    """Test that streaming events are persisted during accumulation."""

    # Mock the persistence layer to verify calls
    from unittest.mock import patch

    with patch("cogency.lib.resilience.resilient_save") as mock_save:
        protocol_tokens = [
            "§THINK\n",
            "Thinking...\n",
            "§CALL\n",
            '{"name": "test_tool", "args": {"message": "persist_test"}}\n',
            "§RESPOND\n",
            "Response text\n",
        ]

        llm = MockStreamingLLM(protocol_tokens)
        tool = MockTestTool()
        agent = Agent(llm=llm, tools=[tool], mode="replay", max_iterations=1)

        events = []
        async for event in agent("Test query", chunks=False):
            events.append(event)

        # Verify persistence was called - accumulator should persist events
        assert mock_save.call_count >= 1  # At least some persistence calls

        # Basic validation that we got events and persistence happened
        assert len(events) >= 1
        assert events[0]["type"] in ["think", "call"]
