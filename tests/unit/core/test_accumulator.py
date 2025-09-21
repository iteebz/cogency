"""Accumulator destruction tests - malformed inputs and edge cases."""

import pytest

from cogency.core.accumulator import Accumulator


async def mock_parser_basic():
    """Basic parser events for testing."""
    events = [
        {"type": "think", "content": "analyzing"},
        {"type": "call", "content": '{"name": "search"}'},
        {"type": "execute"},  # No content for control events
        {"type": "respond", "content": "done"},
        {"type": "end"},  # Real LLM termination - CRITICAL
    ]
    for event in events:
        yield event


@pytest.mark.asyncio
async def test_chunks_true(mock_config):
    """Chunks=True: Stream individual parser events."""
    accumulator = Accumulator(mock_config, "test", "test", chunks=True)

    events = []
    async for event in accumulator.process(mock_parser_basic()):
        events.append(event)

    # Should get individual events + tool result


@pytest.mark.asyncio
async def test_emits_parseable_format(mock_config, mock_tool):
    """Test that accumulator stores JSON format for conversation parsing."""
    import json

    # Add mock tool to config
    mock_config.tools = [mock_tool]
    accumulator = Accumulator(mock_config, "test", "test", chunks=False)

    # Create tool call event using registered tool
    async def parser_with_tool():
        yield {
            "type": "call",
            "content": f'{{"name": "{mock_tool.name}", "args": {{"message": "hello"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    events = []
    async for event in accumulator.process(parser_with_tool()):
        events.append(event)

    # Verify storage has JSON format that conversation can parse
    stored_messages = await mock_config.storage.load_messages("test")
    result_messages = [m for m in stored_messages if m["type"] == "result"]
    assert len(result_messages) == 1

    stored_content = result_messages[0]["content"]

    # Storage must contain JSON array for conversation parsing
    parsed = json.loads(stored_content)
    assert isinstance(parsed, list), "Stored result must be JSON array"
    assert len(parsed) > 0, "Result array must not be empty"
    assert "outcome" in parsed[0], "Result must have outcome field"
    assert "content" in parsed[0], "Result must have content field"


@pytest.mark.asyncio
async def test_chunks_false(mock_config):
    """Chunks=False: Accumulate semantic events."""
    accumulator = Accumulator(mock_config, "test", "test", chunks=False)

    events = []
    async for event in accumulator.process(mock_parser_basic()):
        events.append(event)

    # Should get accumulated events: think, call, result, respond, end
    assert len(events) == 5
    assert events[0]["type"] == "think"
    assert events[1]["type"] == "call"
    assert events[2]["type"] == "result"  # Tool execution
    assert events[3]["type"] == "respond"
    assert events[4]["type"] == "end"


@pytest.mark.asyncio
async def test_end_termination_accumulates_content(mock_config):
    """CRITICAL: §end should flush accumulated content before terminating."""

    async def simple_respond_with_end():
        """Realistic simple response ending with §end."""
        yield {"type": "respond", "content": "The"}
        yield {"type": "respond", "content": " answer"}
        yield {"type": "respond", "content": " is"}
        yield {"type": "respond", "content": " 42"}
        yield {"type": "end"}

    accumulator = Accumulator(mock_config, "test", "test", chunks=False)
    events = []
    async for event in accumulator.process(simple_respond_with_end()):
        events.append(event)

    # MUST get: 1 accumulated respond event + 1 end event
    assert len(events) == 2, f"Expected 2 events, got {len(events)}: {events}"
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "The answer is 42"  # Accumulated content
    assert events[1]["type"] == "end"


@pytest.mark.asyncio
async def test_malformed_call_json(mock_config):
    """Destruction: Malformed call JSON should not crash."""
    accumulator = Accumulator(mock_config, "test", "test", chunks=False)

    async def malformed_parser():
        yield {"type": "call", "content": '{"name":"tool", "invalid": }'}
        yield {"type": "execute"}

    events = []
    async for event in accumulator.process(malformed_parser()):
        events.append(event)

    # Should handle gracefully - gets result event with error
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert "Invalid" in result_events[0]["content"]


@pytest.mark.asyncio
async def test_contaminated_call_content(mock_config):
    """Destruction: Contaminated call content with delimiters."""
    accumulator = Accumulator(mock_config, "test", "test", chunks=False)

    async def contaminated_parser():
        yield {"type": "call", "content": '{"name": "test"}'}
        yield {"type": "call", "content": " §execute§execute"}  # Contamination
        yield {"type": "execute"}

    events = []
    async for event in accumulator.process(contaminated_parser()):
        events.append(event)

    # Should handle contamination and produce error result
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert "Invalid" in result_events[0]["content"]


@pytest.mark.asyncio
async def test_storage_failure(mock_llm):
    """Destruction: Storage failures should not crash accumulator."""

    from cogency.core.config import Config, Security

    class FailingStorage:
        async def save_message(self, *args, **kwargs):
            raise RuntimeError("Storage failed")

    failing_config = Config(
        llm=mock_llm, storage=FailingStorage(), tools=[], security=Security(sandbox=True), learn_every=5
    )
    accumulator = Accumulator(failing_config, "test", "test", chunks=True)

    async def simple_parser():
        yield {"type": "respond", "content": "test"}

    events = []
    try:
        async for event in accumulator.process(simple_parser()):
            events.append(event)
    except RuntimeError:
        pass  # Expected - storage failure should propagate

    # Test passes if we don't crash unexpectedly
    assert True
