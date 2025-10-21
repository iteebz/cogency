import pytest

from cogency.core.accumulator import Accumulator
from cogency.core.config import Config, Security
from cogency.core.parser import parse_tokens


@pytest.mark.asyncio
async def test_flow(mock_llm, mock_config, mock_tool):
    mock_llm.set_response_tokens(
        [
            "§think: I need to call a tool.\n",
            '§call: {"name": "test_tool", "args": {"message": "hello world"}}\n',
            "§execute\n",
        ]
    )

    config = Config(
        llm=mock_config.llm,
        storage=mock_config.storage,
        tools=[mock_tool()],
        security=Security(),
    )

    parser_events = parse_tokens(mock_llm.stream([]))
    accumulator = Accumulator("test_user", "test_conv", execution=config.execution, chunks=False)
    events = [event async for event in accumulator.process(parser_events)]

    assert len(events) > 0
    event_types = [e["type"] for e in events]
    assert "think" in event_types
    assert "result" in event_types
