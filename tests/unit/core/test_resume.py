from unittest.mock import Mock, patch

import pytest

from cogency import resume
from cogency.core.config import Config
from cogency.core.errors import LLMError
from cogency.lib.sqlite import SQLite


@pytest.mark.asyncio
async def test_requires_websocket():
    mock_llm = Mock(spec=[])
    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=1)

    with pytest.raises(LLMError, match="Resume mode requires WebSocket support"):
        await resume.stream("test", "user", "conv", config=config).__anext__()


@pytest.mark.asyncio
async def test_max_iterations_exceeded(mock_llm, mock_config):
    """Multiple events in single turn should not exceed iteration limit."""
    mock_llm.set_response_tokens(["1", "2"])
    mock_config.llm = mock_llm
    mock_config.max_iterations = 1

    events = []
    async for event in resume.stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "respond" for e in events)


@pytest.mark.asyncio
async def test_session_persistence(tmp_path, mock_llm, mock_config):
    mock_llm.set_response_tokens(["Test response"])
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
    with patch("cogency.resume.log_response") as mock_log_response:
        async for event in resume.stream("test query", "user", "conv", config=mock_config):
            events.append(event)

        assert mock_log_response.called  # Assert log_response was called
    assert len(connect_calls) == 1
    assert len(events) > 0
    assert any(e["type"] == "respond" for e in events)


@pytest.mark.asyncio
async def test_stream_ends_without_explicit_end(mock_llm, mock_config):
    mock_llm.set_response_tokens(["This is a response."])
    mock_config.llm = mock_llm

    events = []
    async for event in resume.stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "respond" for e in events)


@pytest.mark.asyncio
async def test_notification_failure_logged(mock_llm, mock_config):
    mock_llm.set_response_tokens(["response"])
    mock_config.llm = mock_llm

    async def failing_notifications():
        raise RuntimeError("Notification source unavailable")

    mock_config.notifications = failing_notifications

    events = []
    with patch("cogency.resume.logger.warning") as mock_warning:
        async for event in resume.stream("test", "user", "conv", config=mock_config):
            events.append(event)

        mock_warning.assert_called_once()
        assert "Notification source failed" in str(mock_warning.call_args)

    assert any(e["type"] == "respond" for e in events)


@pytest.mark.asyncio
async def test_notifications_appended_to_messages(mock_llm, mock_config):
    mock_llm.set_response_tokens(["response"])
    mock_config.llm = mock_llm

    notifications_called = []

    async def working_notifications():
        notifications_called.append(True)
        return ["Alert: system update", "Reminder: check logs"]

    mock_config.notifications = working_notifications

    connect_messages = []
    original_connect = mock_llm.connect

    async def track_connect(messages):
        connect_messages.extend(messages)
        return await original_connect(messages)

    mock_llm.connect = track_connect

    events = []
    async for event in resume.stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert notifications_called
    system_contents = [m["content"] for m in connect_messages if m.get("role") == "system"]
    assert "Alert: system update" in system_contents
    assert "Reminder: check logs" in system_contents


@pytest.mark.asyncio
async def test_end_event_emits_metrics(mock_config, resume_llm):
    mock_config.llm = resume_llm([["<end>"]])

    events = []
    async for event in resume.stream("test", "user", "conv", config=mock_config):
        events.append(event)

    event_types = [e["type"] for e in events]
    assert "metric" in event_types
    assert "end" in event_types
    assert event_types.index("metric") < event_types.index("end")


@pytest.mark.asyncio
async def test_websocket_continuation_error(mock_llm, mock_config):
    mock_llm.set_response_tokens(["partial"])
    mock_llm.set_continuation_error(RuntimeError("Connection lost"))
    mock_config.llm = mock_llm

    with pytest.raises(LLMError, match="WebSocket continuation failed"):
        async for _ in resume.stream("test", "user", "conv", config=mock_config):
            pass
