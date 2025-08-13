"""Test lifecycle decorator prevents observability regression."""

from unittest.mock import patch

import pytest

from cogency.events.lifecycle import lifecycle


@pytest.fixture
def mock_emit():
    """Mock emit function to capture events."""
    events = []

    def capture_emit(event_type, **kwargs):
        events.append({"type": event_type, **kwargs})

    with patch("cogency.events.lifecycle.emit", side_effect=capture_emit):
        yield events


@pytest.mark.asyncio
async def test_async_lifecycle_events(mock_emit):
    """@lifecycle emits start/complete for async functions."""

    @lifecycle("test", operation="run")
    async def async_func():
        return "result"

    result = await async_func()

    assert result == "result"
    assert len(mock_emit) == 2

    start_event = mock_emit[0]
    assert start_event["type"] == "test"
    assert start_event["status"] == "start"
    assert start_event["operation"] == "run"

    complete_event = mock_emit[1]
    assert complete_event["type"] == "test"
    assert complete_event["status"] == "complete"
    assert complete_event["operation"] == "run"


def test_sync_lifecycle_events(mock_emit):
    """@lifecycle emits start/complete for sync functions."""

    @lifecycle("test", operation="run")
    def sync_func():
        return "result"

    result = sync_func()

    assert result == "result"
    assert len(mock_emit) == 2
    assert mock_emit[0]["status"] == "start"
    assert mock_emit[1]["status"] == "complete"


@pytest.mark.asyncio
async def test_lifecycle_error_events(mock_emit):
    """@lifecycle emits error events on exceptions."""

    @lifecycle("test", operation="fail")
    async def failing_func():
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        await failing_func()

    assert len(mock_emit) == 2
    assert mock_emit[0]["status"] == "start"
    assert mock_emit[1]["status"] == "error"
    assert mock_emit[1]["error"] == "test error"
