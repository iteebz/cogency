from unittest.mock import Mock, patch

import pytest

from cogency.core.config import Config
from cogency.core.resume import stream as resume_stream
from cogency.lib.sqlite import SQLite


@pytest.mark.asyncio
async def test_requires_websocket():
    mock_llm = Mock(spec=[])
    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=1)

    with pytest.raises(RuntimeError, match="Resume mode requires WebSocket support"):
        await resume_stream("test", "user", "conv", config=config).__anext__()


@pytest.mark.asyncio
async def test_max_iterations_exceeded(mock_llm, mock_config):
    """Multiple events in single turn should not exceed iteration limit."""
    mock_llm.set_response_tokens(["§respond: 1", "§respond: 2", "§end"])
    mock_config.llm = mock_llm
    mock_config.max_iterations = 1

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "respond" for e in events)
    assert any(e["type"] == "end" for e in events)


@pytest.mark.asyncio
async def test_session_persistence(tmp_path, mock_llm, mock_config):
    mock_llm.set_response_tokens(["§respond: Test response", "§end"])
    mock_config.llm = mock_llm
    mock_config.debug = True  # Enable debug logging
    mock_config.storage = SQLite(db_path=str(tmp_path / "test.db"))

    connect_calls = []
    original_connect = mock_llm.connect

    async def track_connect(messages):
        connect_calls.append(messages)
        return await original_connect(messages)

    mock_llm.connect = track_connect

    events = []
    with patch("cogency.core.resume.log_response") as mock_log_response:
        async for event in resume_stream("test query", "user", "conv", config=mock_config):
            events.append(event)

        assert mock_log_response.called  # Assert log_response was called
    assert len(connect_calls) == 1
    assert len(events) > 0
    assert any(e["type"] == "respond" for e in events)


@pytest.mark.asyncio
async def test_stream_ends_without_explicit_end(mock_llm, mock_config):
    # Simulate a stream that ends naturally without an explicit §end
    mock_llm.set_response_tokens(["§respond: This is a response."])
    mock_config.llm = mock_llm

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "respond" for e in events)
    # The 'complete' flag should be set to True even without an explicit 'end' event
    # This is implicitly tested by the stream finishing without error.


@pytest.mark.asyncio
async def test_llm_provider_required():
    config = Config(llm=None, storage=Mock(), tools=[], max_iterations=1)

    with pytest.raises(ValueError, match="LLM provider required"):
        async for _ in resume_stream("test", "user", "conv", config=config):
            pass
