import pytest

from cogency.core.accumulator import Accumulator
from cogency.core.config import Config, Security


async def basic_parser():
    yield {"type": "think", "content": "analyzing"}
    yield {"type": "call", "content": '{"name": "search"}'}
    yield {"type": "execute"}
    yield {"type": "respond", "content": "done"}
    yield {"type": "end"}


@pytest.mark.asyncio
async def test_chunks_true(mock_config):
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="token")
    events = [event async for event in accumulator.process(basic_parser())]  # type: ignore[arg-type]
    types = [e["type"] for e in events]
    assert "think" in types
    assert "call" in types
    assert "respond" in types
    assert "end" in types


@pytest.mark.asyncio
async def test_respond_chunked(mock_config):
    """respond/think chunk in token mode but persist once."""

    async def chunked_respond():
        yield {"type": "respond", "content": "hello"}
        yield {"type": "respond", "content": " world"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="token")
    events = [event async for event in accumulator.process(chunked_respond())]  # type: ignore[arg-type]

    respond_events = [e for e in events if e["type"] == "respond"]
    assert len(respond_events) == 2
    assert respond_events[0]["content"] == "hello"
    assert respond_events[1]["content"] == " world"

    stored = await mock_config.storage.load_messages("test")
    respond_stored = [m for m in stored if m["type"] == "respond"]
    assert len(respond_stored) == 1
    assert respond_stored[0]["content"] == "hello world"

    # Control events are no longer persisted; only semantic turns are stored.
    assert mock_config.storage.events == []


@pytest.mark.asyncio
async def test_chunks_false(mock_config):
    """stream='event': calls are processed immediately, not accumulated"""
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")
    events = [event async for event in accumulator.process(basic_parser())]  # type: ignore[arg-type]

    types = [e["type"] for e in events]
    assert "think" in types
    assert "call" in types
    assert "execute" in types
    assert "result" in types
    assert "respond" in types
    assert "end" in types


@pytest.mark.asyncio
async def test_end_flushes(mock_config):
    async def respond_with_end():
        yield {"type": "respond", "content": "The"}
        yield {"type": "respond", "content": " answer"}
        yield {"type": "respond", "content": " is"}
        yield {"type": "respond", "content": " 42"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")
    events = [event async for event in accumulator.process(respond_with_end())]  # type: ignore[arg-type]

    assert len(events) == 2
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "The answer is 42"
    assert events[1]["type"] == "end"


@pytest.mark.asyncio
async def test_storage_format(mock_config, mock_tool):
    import json

    tool_instance = mock_tool()
    mock_config.tools = [tool_instance]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser_with_tool():
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "hello"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    [event async for event in accumulator.process(parser_with_tool())]  # type: ignore[arg-type]

    stored_messages = await mock_config.storage.load_messages("test")
    result_messages = [m for m in stored_messages if m["type"] == "result"]
    assert len(result_messages) == 1

    content = result_messages[0]["content"]
    assert content.startswith("[")
    assert content.endswith("]")

    parsed = json.loads(content)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["tool"] == tool_instance.name
    assert parsed[0]["status"] == "success"
    assert "content" in parsed[0]


@pytest.mark.asyncio
async def test_sequential_batch(mock_config, mock_tool):
    """Multiple tools execute sequentially in order."""
    tool_instance = mock_tool()
    mock_config.tools = [tool_instance]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser():
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "first"}}}}',
        }
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "second"}}}}',
        }
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "third"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    events = [event async for event in accumulator.process(parser())]  # type: ignore[arg-type]
    result_events = [e for e in events if e["type"] == "result"]

    assert len(result_events) == 1

    import json

    content = result_events[0]["content"]
    json_str = content.replace("<results>\n", "").replace("\n</results>", "")
    results = json.loads(json_str)

    assert len(results) == 3
    assert results[0]["content"] == "Full details: first"
    assert results[1]["content"] == "Full details: second"
    assert results[2]["content"] == "Full details: third"


@pytest.mark.asyncio
async def test_storage_failure_propagates(mock_llm, failing_storage):
    config = Config(llm=mock_llm, storage=failing_storage, tools=[], security=Security())
    accumulator = Accumulator("test", "test", execution=config.execution, stream="token")

    async def simple_parser():
        yield {"type": "respond", "content": "test"}

    with pytest.raises(RuntimeError):
        async for _event in accumulator.process(simple_parser()):  # type: ignore[arg-type]
            pass


@pytest.mark.asyncio
async def test_circuit_breaker_terminates(mock_config, mock_tool):
    mock_config.tools = [mock_tool()]
    accumulator = Accumulator(
        "test", "test", execution=mock_config.execution, stream="event", max_failures=3
    )

    async def failing_parser():
        for _ in range(5):
            yield {"type": "call", "content": '{"name": "invalid_tool", "args": {}}'}
            yield {"type": "execute"}

    events = [event async for event in accumulator.process(failing_parser())]  # type: ignore[arg-type]
    result_events = [e for e in events if e["type"] == "result"]
    end_events = [e for e in events if e["type"] == "end"]

    assert len(end_events) == 1
    assert len(result_events) <= 4
    payload = result_events[-1]["payload"]
    assert payload is not None
    assert "Max failures" in payload["outcome"]


@pytest.mark.asyncio
async def test_persistence_policy(mock_config, mock_tool):
    """Verify only conversation events are persisted (not control flow or metrics)."""
    from cogency.core.accumulator import PERSISTABLE_EVENTS

    tool_instance = mock_tool()
    mock_config.tools = [tool_instance]
    accumulator = Accumulator("user_1", "conv_123", execution=mock_config.execution, stream="event")

    async def all_event_types():
        yield {"type": "user", "content": "test query"}
        yield {"type": "think", "content": "thinking"}
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "test"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "respond", "content": "response"}
        yield {"type": "end"}

    [event async for event in accumulator.process(all_event_types())]  # type: ignore[arg-type]

    stored = await mock_config.storage.load_messages("conv_123")
    stored_types = {m["type"] for m in stored}

    # Verify persistence policy constant matches actual behavior
    for event_type in PERSISTABLE_EVENTS:
        assert event_type in stored_types, f"{event_type} should be persisted"

    # Verify control flow and metrics are NOT persisted
    assert "execute" not in stored_types
    assert "end" not in stored_types
    assert "metrics" not in stored_types


@pytest.mark.asyncio
async def test_result_has_content(mock_config, mock_tool):
    """Result events have content field."""
    tool_instance = mock_tool()
    mock_config.tools = [tool_instance]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser():
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "test"}}}}',
        }
        yield {"type": "execute"}

    events = [event async for event in accumulator.process(parser())]  # type: ignore[arg-type]
    result_events = [e for e in events if e["type"] == "result"]

    assert len(result_events) == 1
    assert "content" in result_events[0]
    assert result_events[0]["content"]


@pytest.mark.asyncio
async def test_token_streaming(mock_config):
    """stream='token' yields individual events."""

    async def chunked_parser():
        yield {"type": "respond", "content": "Hello"}
        yield {"type": "respond", "content": " world"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="token")
    events = [event async for event in accumulator.process(chunked_parser())]  # type: ignore[arg-type]

    respond_events = [e for e in events if e["type"] == "respond"]
    assert len(respond_events) == 2, "stream='token' should yield multiple token events"


@pytest.mark.asyncio
async def test_semantic_accumulation(mock_config):
    """stream='event' yields accumulated semantic events."""

    async def chunked_parser():
        yield {"type": "respond", "content": "Hello"}
        yield {"type": "respond", "content": " world"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")
    events = [event async for event in accumulator.process(chunked_parser())]  # type: ignore[arg-type]

    respond_events = [e for e in events if e["type"] == "respond"]
    assert len(respond_events) == 1, "stream='event' should yield single accumulated event"
    assert respond_events[0]["content"] == "Hello world"


@pytest.mark.asyncio
async def test_result_format_spec(mock_config, mock_tool):
    """Result format matches protocol spec."""
    import json

    tool_instance = mock_tool()
    mock_config.tools = [tool_instance]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser():
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "test"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    events = [event async for event in accumulator.process(parser())]  # type: ignore[arg-type]
    result_events = [e for e in events if e["type"] == "result"]

    result_event = result_events[0]
    content = result_event["content"]

    assert content.startswith("[")
    assert content.endswith("]")

    array = json.loads(content)

    assert isinstance(array, list)
    assert len(array) == 1

    item = array[0]
    assert "tool" in item
    assert "status" in item
    assert "content" in item
    assert item["status"] in ["success", "failure"]
    assert item["tool"] == tool_instance.name


@pytest.mark.asyncio
async def test_result_metadata(mock_config, mock_tool):
    """Result event has execution metadata."""
    tool_instance = mock_tool()
    mock_config.tools = [tool_instance]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser():
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "test"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    events = [event async for event in accumulator.process(parser())]  # type: ignore[arg-type]
    result_events = [e for e in events if e["type"] == "result"]

    result_event = result_events[0]
    payload = result_event["payload"]
    assert payload is not None

    assert "tools_executed" in payload
    assert "success_count" in payload
    assert "failure_count" in payload
    assert payload["tools_executed"] == 1
    assert payload["success_count"] == 1
    assert payload["failure_count"] == 0


@pytest.mark.asyncio
async def test_mixed_success_failure_batch(mock_config, mock_tool):
    """Batch with mixed success/failure executes all, counts correctly."""
    success_tool = mock_tool()
    fail_tool = mock_tool().configure(name="fail_tool", should_fail=True)
    mock_config.tools = [success_tool, fail_tool]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser():
        yield {
            "type": "call",
            "content": f'{{"name": "{success_tool.name}", "args": {{"message": "ok"}}}}',
        }
        yield {
            "type": "call",
            "content": f'{{"name": "{fail_tool.name}", "args": {{"message": "bad"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    events = [event async for event in accumulator.process(parser())]  # type: ignore[arg-type]
    result_events = [e for e in events if e["type"] == "result"]

    assert len(result_events) == 1
    payload = result_events[0]["payload"]
    assert payload is not None
    assert payload["tools_executed"] == 2
    assert payload["success_count"] == 1
    assert payload["failure_count"] == 1

    import json

    content = result_events[0]["content"]
    json_str = content.replace("<results>\n", "").replace("\n</results>", "")
    results = json.loads(json_str)
    assert results[0]["status"] == "success"
    assert results[1]["status"] == "failure"


@pytest.mark.asyncio
async def test_empty_tool_list_skips_execution(mock_config):
    """No tools available, call event doesn't execute."""
    mock_config.tools = []
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser():
        yield {
            "type": "call",
            "content": '{"name": "missing_tool", "args": {}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    events = [event async for event in accumulator.process(parser())]  # type: ignore[arg-type]
    result_events = [e for e in events if e["type"] == "result"]

    assert len(result_events) == 1
    payload = result_events[0]["payload"]
    assert payload is not None
    assert payload["failure_count"] == 1
