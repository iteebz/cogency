import pytest

from cogency.core.accumulator import Accumulator
from cogency.core.codec import ToolParseError
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
    events = [event async for event in accumulator.process(basic_parser())]
    assert len(events) > 0


@pytest.mark.asyncio
async def test_call_not_chunked(mock_config):
    """call/result/cancelled/metric always complete, even when stream='token'"""

    async def chunked_call():
        yield {"type": "call", "content": '{"name"'}
        yield {"type": "call", "content": ': "search"'}
        yield {"type": "call", "content": ', "args": {}}'}
        yield {"type": "execute"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="token")
    events = [event async for event in accumulator.process(chunked_call())]

    call_events = [e for e in events if e["type"] == "call"]
    assert len(call_events) == 1
    assert call_events[0]["content"] == '{"name": "search", "args": {}}'


@pytest.mark.asyncio
async def test_respond_chunked_enabled(mock_config):
    """respond/think stream naturally when stream='token' but persist only once"""

    async def chunked_respond():
        yield {"type": "respond", "content": "hello"}
        yield {"type": "respond", "content": " world"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="token")
    events = [event async for event in accumulator.process(chunked_respond())]

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
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")
    events = [event async for event in accumulator.process(basic_parser())]
    assert len(events) == 6
    assert events[0]["type"] == "think"
    assert events[1]["type"] == "call"
    assert events[2]["type"] == "execute"
    assert events[3]["type"] == "result"
    assert events[4]["type"] == "respond"
    assert events[5]["type"] == "end"


@pytest.mark.asyncio
async def test_end_flushes(mock_config):
    async def respond_with_end():
        yield {"type": "respond", "content": "The"}
        yield {"type": "respond", "content": " answer"}
        yield {"type": "respond", "content": " is"}
        yield {"type": "respond", "content": " 42"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")
    events = [event async for event in accumulator.process(respond_with_end())]

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

    [event async for event in accumulator.process(parser_with_tool())]

    stored_messages = await mock_config.storage.load_messages("test")
    result_messages = [m for m in stored_messages if m["type"] == "result"]
    assert len(result_messages) == 1

    content = result_messages[0]["content"]
    assert content.startswith("<results>")
    assert content.endswith("</results>")

    json_str = content.replace("<results>\n", "").replace("\n</results>", "")
    parsed = json.loads(json_str)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["tool"] == tool_instance.name
    assert parsed[0]["status"] == "success"
    assert "content" in parsed[0]


@pytest.mark.asyncio
async def test_malformed_call_json(mock_config):
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def malformed_parser():
        yield {"type": "call", "content": '{"name":"tool", "invalid": }'}
        yield {"type": "execute"}

    with pytest.raises(ToolParseError):
        [event async for event in accumulator.process(malformed_parser())]


@pytest.mark.asyncio
async def test_contaminated_content(mock_config):
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def contaminated_parser():
        yield {"type": "call", "content": '{"name": "file_write", "args": {"file": "test.py"}'}
        yield {"type": "call", "content": " §execute§execute"}
        yield {"type": "execute"}

    with pytest.raises(ToolParseError):
        [event async for event in accumulator.process(contaminated_parser())]


@pytest.mark.asyncio
async def test_storage_failure_propagates(mock_llm, failing_storage):
    config = Config(llm=mock_llm, storage=failing_storage, tools=[], security=Security())
    accumulator = Accumulator("test", "test", execution=config.execution, stream="token")

    async def simple_parser():
        yield {"type": "respond", "content": "test"}

    with pytest.raises(RuntimeError):
        async for _event in accumulator.process(simple_parser()):
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

    events = [event async for event in accumulator.process(failing_parser())]
    result_events = [e for e in events if e["type"] == "result"]
    end_events = [e for e in events if e["type"] == "end"]

    assert len(end_events) == 1
    assert len(result_events) <= 4
    assert "Max failures" in result_events[-1]["payload"]["outcome"]


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

    [event async for event in accumulator.process(all_event_types())]

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
async def test_result_event_has_content(mock_config, mock_tool):
    """Result events must have content field for resume mode websocket injection."""
    tool_instance = mock_tool()
    mock_config.tools = [tool_instance]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")

    async def parser():
        yield {
            "type": "call",
            "content": f'{{"name": "{tool_instance.name}", "args": {{"message": "test"}}}}',
        }
        yield {"type": "execute"}

    events = [event async for event in accumulator.process(parser())]
    result_events = [e for e in events if e["type"] == "result"]

    assert len(result_events) == 1
    assert "content" in result_events[0]
    assert result_events[0]["content"]


@pytest.mark.asyncio
async def test_chunks_true_yields_token_events(mock_config):
    """chunks=True yields individual token events (contract for stream='token')."""

    async def chunked_parser():
        yield {"type": "respond", "content": "Hello"}
        yield {"type": "respond", "content": " world"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="token")
    events = [event async for event in accumulator.process(chunked_parser())]

    respond_events = [e for e in events if e["type"] == "respond"]
    assert len(respond_events) == 2, "stream='token' should yield multiple token events"


@pytest.mark.asyncio
async def test_chunks_false_yields_semantic_events(mock_config):
    """chunks=False yields single accumulated semantic events (contract for stream='event')."""

    async def chunked_parser():
        yield {"type": "respond", "content": "Hello"}
        yield {"type": "respond", "content": " world"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, stream="event")
    events = [event async for event in accumulator.process(chunked_parser())]

    respond_events = [e for e in events if e["type"] == "respond"]
    assert len(respond_events) == 1, "stream='event' should yield single accumulated event"
    assert respond_events[0]["content"] == "Hello world"


@pytest.mark.asyncio
async def test_result_injection_format_spec_compliance(mock_config, mock_tool):
    """Result injection format matches XML protocol spec exactly."""
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

    events = [event async for event in accumulator.process(parser())]
    result_events = [e for e in events if e["type"] == "result"]

    result_event = result_events[0]
    content = result_event["content"]

    assert content.startswith("<results>")
    assert content.endswith("</results>")

    json_str = content.replace("<results>\n", "").replace("\n</results>", "")
    array = json.loads(json_str)

    assert isinstance(array, list)
    assert len(array) == 1

    item = array[0]
    assert "tool" in item
    assert "status" in item
    assert "content" in item
    assert item["status"] in ["success", "failure"]
    assert item["tool"] == tool_instance.name


@pytest.mark.asyncio
async def test_result_event_metadata(mock_config, mock_tool):
    """Result event has metadata payload with execution summary."""
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

    events = [event async for event in accumulator.process(parser())]
    result_events = [e for e in events if e["type"] == "result"]

    result_event = result_events[0]
    payload = result_event["payload"]

    assert "tools_executed" in payload
    assert "success_count" in payload
    assert "failure_count" in payload
    assert payload["tools_executed"] == 1
    assert payload["success_count"] == 1
    assert payload["failure_count"] == 0
