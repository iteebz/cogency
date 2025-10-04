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
    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=True)
    events = [event async for event in accumulator.process(basic_parser())]
    assert len(events) > 0


@pytest.mark.asyncio
async def test_call_not_chunked(mock_config):
    """call/result/cancelled/metric always complete, even when chunks=True"""

    async def chunked_call():
        yield {"type": "call", "content": '{"name"'}
        yield {"type": "call", "content": ': "search"'}
        yield {"type": "call", "content": ', "args": {}}'}
        yield {"type": "execute"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=True)
    events = [event async for event in accumulator.process(chunked_call())]

    call_events = [e for e in events if e["type"] == "call"]
    assert len(call_events) == 1
    assert call_events[0]["content"] == '{"name": "search", "args": {}}'


@pytest.mark.asyncio
async def test_respond_chunked_when_enabled(mock_config):
    """respond/think stream naturally when chunks=True but persist only once"""

    async def chunked_respond():
        yield {"type": "respond", "content": "hello"}
        yield {"type": "respond", "content": " world"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=True)
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
    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=False)
    events = [event async for event in accumulator.process(basic_parser())]
    assert len(events) == 5
    assert events[0]["type"] == "think"
    assert events[1]["type"] == "call"
    assert events[2]["type"] == "result"
    assert events[3]["type"] == "respond"
    assert events[4]["type"] == "end"


@pytest.mark.asyncio
async def test_end_flushes(mock_config):
    async def respond_with_end():
        yield {"type": "respond", "content": "The"}
        yield {"type": "respond", "content": " answer"}
        yield {"type": "respond", "content": " is"}
        yield {"type": "respond", "content": " 42"}
        yield {"type": "end"}

    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=False)
    events = [event async for event in accumulator.process(respond_with_end())]

    assert len(events) == 2
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "The answer is 42"
    assert events[1]["type"] == "end"


@pytest.mark.asyncio
async def test_storage_format(mock_config, mock_tool):
    import json

    mock_config.tools = [mock_tool]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=False)

    async def parser_with_tool():
        yield {
            "type": "call",
            "content": f'{{"name": "{mock_tool.name}", "args": {{"message": "hello"}}}}',
        }
        yield {"type": "execute"}
        yield {"type": "end"}

    [event async for event in accumulator.process(parser_with_tool())]

    stored_messages = await mock_config.storage.load_messages("test")
    result_messages = [m for m in stored_messages if m["type"] == "result"]
    assert len(result_messages) == 1

    parsed = json.loads(result_messages[0]["content"])
    assert isinstance(parsed, dict)
    assert "outcome" in parsed
    assert "content" in parsed


@pytest.mark.asyncio
async def test_malformed_call_json(mock_config):
    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=False)

    async def malformed_parser():
        yield {"type": "call", "content": '{"name":"tool", "invalid": }'}
        yield {"type": "execute"}

    events = [event async for event in accumulator.process(malformed_parser())]
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert "Invalid" in result_events[0]["payload"]["outcome"]


@pytest.mark.asyncio
async def test_contaminated_content(mock_config):
    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=False)

    async def contaminated_parser():
        yield {"type": "call", "content": '{"name": "file_write", "args": {"file": "test.py"}'}
        yield {"type": "call", "content": " §execute§execute"}
        yield {"type": "execute"}

    events = [event async for event in accumulator.process(contaminated_parser())]
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert "Invalid" in result_events[0]["payload"]["outcome"]


@pytest.mark.asyncio
async def test_storage_failure_propagates(mock_llm):
    class FailingStorage:
        async def save_message(self, *args, **kwargs):
            raise RuntimeError("Storage failed")

        async def save_event(self, *args, **kwargs):
            raise RuntimeError("Event storage failed")

    config = Config(llm=mock_llm, storage=FailingStorage(), tools=[], security=Security())
    accumulator = Accumulator("test", "test", execution=config.execution, chunks=True)

    async def simple_parser():
        yield {"type": "respond", "content": "test"}

    with pytest.raises(RuntimeError):
        async for _event in accumulator.process(simple_parser()):
            pass


@pytest.mark.asyncio
async def test_circuit_breaker_terminates(mock_config, mock_tool):
    mock_config.tools = [mock_tool]
    accumulator = Accumulator(
        "test", "test", execution=mock_config.execution, chunks=False, max_failures=3
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

    mock_config.tools = [mock_tool]
    accumulator = Accumulator("user_1", "conv_123", execution=mock_config.execution, chunks=False)

    async def all_event_types():
        yield {"type": "user", "content": "test query"}
        yield {"type": "think", "content": "thinking"}
        yield {
            "type": "call",
            "content": f'{{"name": "{mock_tool.name}", "args": {{"message": "test"}}}}',
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
    mock_config.tools = [mock_tool]
    accumulator = Accumulator("test", "test", execution=mock_config.execution, chunks=False)

    async def parser():
        yield {
            "type": "call",
            "content": f'{{"name": "{mock_tool.name}", "args": {{"message": "test"}}}}',
        }
        yield {"type": "execute"}

    events = [event async for event in accumulator.process(parser())]
    result_events = [e for e in events if e["type"] == "result"]

    assert len(result_events) == 1
    assert "content" in result_events[0]
    assert result_events[0]["content"]
    assert "§result:" in result_events[0]["content"]
