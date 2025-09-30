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
async def test_end_flushes_accumulated_content(mock_config):
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
async def test_result_format_for_storage(mock_config, mock_tool):
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
async def test_contaminated_call_content(mock_config):
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

    config = Config(
        llm=mock_llm, storage=FailingStorage(), tools=[], security=Security(), learn_every=5
    )
    accumulator = Accumulator("test", "test", execution=config.execution, chunks=True)

    async def simple_parser():
        yield {"type": "respond", "content": "test"}

    with pytest.raises(RuntimeError):
        async for _event in accumulator.process(simple_parser()):
            pass
