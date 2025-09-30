from unittest.mock import Mock

import pytest

from cogency.core.config import Config
from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_requires_websocket():
    mock_llm = Mock(spec=[])
    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=1)

    with pytest.raises(RuntimeError, match="Resume mode requires WebSocket support"):
        async for _ in resume_stream("test", "user", "conv", config=config):
            pass


@pytest.mark.asyncio
async def test_session_persistence(mock_llm, mock_config):
    mock_llm.set_response_tokens(["§respond: Test response", "§end"])
    mock_config.llm = mock_llm

    connect_calls = []
    original_connect = mock_llm.connect

    async def track_connect(messages):
        connect_calls.append(messages)
        return await original_connect(messages)

    mock_llm.connect = track_connect

    events = []
    async for event in resume_stream("test query", "user", "conv", config=mock_config):
        events.append(event)

    assert len(connect_calls) == 1
    assert len(events) > 0
    assert any(e["type"] == "respond" for e in events)
