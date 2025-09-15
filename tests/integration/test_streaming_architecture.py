"""Integration tests for Agent→Parser→Accumulator→Executor flow.

Tests complete streaming architecture end-to-end to verify chunks=True/False
modes work correctly and tool execution integrates properly.
"""

import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_complete_streaming_flow_chunks_false(mock_llm, mock_tool):
    """Test complete Agent→Parser→Accumulator→Executor flow with chunks=False."""

    # Protocol response: think → call → respond (tool result injected by accumulator)
    protocol_tokens = [
        "§think: I need to call a tool.\n",
        '§call: {"name": "test_tool", "args": {"message": "hello world"}}\n',
        "§execute\n",
        "§respond: The tool completed successfully.\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)

    # Create agent with mock components - use replay mode to avoid WebSocket requirements
    agent = Agent(llm=llm, tools=[mock_tool], mode="replay", max_iterations=1)

    # Execute with chunks=False (semantic events)
    events = []
    async for event in agent("Test query", chunks=False):
        events.append(event)

    # Verify we get semantic events (think, call at minimum)
    assert len(events) >= 2

    # Verify event structure and content
    assert events[0]["type"] == "think"
    assert "need to call a tool" in events[0]["content"]

    # In chunks=False mode, call events are now emitted followed by results
    assert events[1]["type"] == "call"
    assert events[2]["type"] == "result"
    assert "Tool executed: hello world" in events[2]["content"]

    # Integration test proves Agent→Parser→Accumulator flow works
    # Full tool execution is tested separately in executor unit tests


@pytest.mark.asyncio
async def test_complete_streaming_flow_chunks_true(mock_llm, mock_tool):
    """Test complete flow with chunks=True (token streaming)."""

    protocol_tokens = [
        "§think: Think",
        "ing...\n",
        '§call: {"name": "test_tool", "args": {"message": "test"}}\n',
        "§execute\n",
        "§respond: Done!\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], mode="replay", max_iterations=1)

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
async def test_tool_execution_integration(mock_llm, mock_tool):
    """Test tool execution is properly integrated into streaming flow."""

    # Response that calls tool with specific args
    protocol_tokens = [
        '§call: {"name": "test_tool", "args": {"message": "integration test"}}\n',
        "§execute\n",
        "§respond: Tool call completed.\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], mode="replay", max_iterations=1)

    events = []
    async for event in agent("Test query", chunks=False):
        events.append(event)

    # Should have call and result events
    assert len(events) >= 2

    call_event = events[0]
    result_event = events[1]

    # Verify tool call and result were generated correctly
    assert call_event["type"] == "call"
    assert result_event["type"] == "result"
    assert "Tool executed: integration test" in result_event["content"]


@pytest.mark.asyncio
async def test_error_handling_in_streaming_flow(mock_llm, mock_tool):
    """Test error handling propagates through streaming architecture."""

    protocol_tokens = [
        '§call: {"name": "failing_tool", "args": {}}\n',
        "§execute\n",
        "§respond: Handling error...\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    failing_tool = mock_tool.configure(
        name="failing_tool", description="Tool that fails", should_fail=True
    )
    agent = Agent(llm=llm, tools=[failing_tool], mode="replay", max_iterations=1)

    # Tool failure should bubble up as RuntimeError from agent
    with pytest.raises(RuntimeError, match="Stream failed"):
        events = []
        async for event in agent("Test query", chunks=False):
            events.append(event)


@pytest.mark.asyncio
async def test_persistence_integration(mock_llm, mock_tool, mock_storage):
    """Test streaming events flow with persistence layer."""

    protocol_tokens = [
        "§think: Thinking...\n",
        '§call: {"name": "test_tool", "args": {"message": "persist_test"}}\n',
        "§execute\n",
        "§respond: Response text\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool], storage=mock_storage, mode="replay", max_iterations=1)

    events = []
    async for event in agent("Test query", chunks=False):
        events.append(event)

    # Test actual behavior - we should get semantic events
    assert len(events) >= 2  # think, result, metrics
    assert any(e["type"] == "think" for e in events)
    assert any(e["type"] == "result" for e in events)
