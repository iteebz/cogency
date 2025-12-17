import pytest

from cogency.lib.telemetry import add_event, persist_events


def test_add_event_appends():
    events = []
    add_event(events, {"type": "user", "content": "a", "timestamp": 1.0})
    add_event(events, {"type": "user", "content": "b", "timestamp": 2.0})
    assert len(events) == 2
    assert events[0]["content"] == "a"
    assert events[1]["content"] == "b"


@pytest.mark.asyncio
async def test_persist_events_saves_to_storage():
    from unittest.mock import AsyncMock

    events = [
        {"type": "metric", "content": "data1", "timestamp": 1.0},
        {"type": "metric", "content": "data2", "timestamp": 2.0},
    ]

    mock_storage = AsyncMock()
    mock_storage.save_event = AsyncMock()

    await persist_events("conv_123", events, mock_storage)  # type: ignore[arg-type]

    assert mock_storage.save_event.call_count == 2
    assert len(events) == 0


@pytest.mark.asyncio
async def test_persist_events_handles_dict_content():
    from unittest.mock import AsyncMock

    events = [{"type": "metric", "content": {"key": "value"}, "timestamp": 1.0}]

    mock_storage = AsyncMock()
    mock_storage.save_event = AsyncMock()

    await persist_events("conv_123", events, mock_storage)  # type: ignore[arg-type]

    mock_storage.save_event.assert_called_once_with(
        conversation_id="conv_123", type="metric", content='{"key": "value"}'
    )


@pytest.mark.asyncio
async def test_persist_events_no_op_on_empty():
    from unittest.mock import AsyncMock

    mock_storage = AsyncMock()

    await persist_events("conv_123", [], mock_storage)

    mock_storage.save_event.assert_not_called()


@pytest.mark.asyncio
async def test_persist_events_continues_on_error():
    from unittest.mock import AsyncMock

    events = [{"type": "metric", "content": "data", "timestamp": 1.0}]

    mock_storage = AsyncMock()
    mock_storage.save_event = AsyncMock(side_effect=RuntimeError("DB fail"))

    await persist_events("conv_123", events, mock_storage)  # type: ignore[arg-type]

    assert len(events) == 1
