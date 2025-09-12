"""Minimal integration test to debug streaming flow."""

import asyncio

import pytest

from cogency.core.accumulator import Accumulator
from cogency.core.config import Config
from cogency.core.parser import parse_tokens
from cogency.core.protocols import LLM, Storage, Tool, ToolResult
from cogency.core.result import Ok


class MockLLM(LLM):
    def __init__(self, response_tokens):
        self.response_tokens = response_tokens

    async def generate(self, messages):
        return Ok("Generated")

    async def connect(self, messages):
        return Ok("connection")

    async def stream(self, connection):
        for token in self.response_tokens:
            yield token
            await asyncio.sleep(0.001)

    async def send(self, session, content):
        return True

    async def receive(self, session):
        for token in self.response_tokens:
            yield token
            await asyncio.sleep(0.001)

    async def close(self, session):
        return True


class MockStorage(Storage):
    async def save_message(self, *args, **kwargs):
        return True

    async def load_messages(self, *args, **kwargs):
        return []

    async def save_profile(self, *args, **kwargs):
        return True

    async def load_profile(self, *args, **kwargs):
        return {}


class MockTool(Tool):
    @property
    def name(self):
        return "test_tool"

    @property
    def description(self):
        return "Test tool"

    @property
    def schema(self):
        return {"message": {}}

    async def execute(self, message="test", **kwargs):
        return Ok(ToolResult(outcome=f"Tool executed: {message}"))


@pytest.mark.asyncio
async def test_parser_accumulator_executor_flow():
    """Test Parser→Accumulator→Executor flow directly."""

    protocol_tokens = [
        "§THINK\n",
        "I need to call a tool.\n",
        "§CALL\n",
        '{"name": "test_tool", "args": {"message": "hello world"}}\n',
        "§RESPOND\n",
        "The tool completed successfully.\n",
    ]

    llm = MockLLM(protocol_tokens)
    storage = MockStorage()
    tool = MockTool()

    config = Config(llm=llm, storage=storage, tools=[tool])

    # Connect and get token stream
    connection = await llm.connect([])
    connection = connection.unwrap()

    # Parse tokens directly
    parser_events = parse_tokens(llm.stream(connection))

    # Process through accumulator
    accumulator = Accumulator(config, "test_user", "test_conv", chunks=False)
    events = []

    async for event in accumulator.process(parser_events):
        events.append(event)
        print(f"Event: {event['type']} - {event['content'][:50]}...")

    print(f"Total events: {len(events)}")

    # Basic validation
    assert len(events) > 0

    # Check we got semantic events
    event_types = [e["type"] for e in events]
    print(f"Event types: {event_types}")

    assert "think" in event_types
    assert "call" in event_types
    assert "respond" in event_types
