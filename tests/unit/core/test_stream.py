"""Stream tests."""

from unittest.mock import patch

import pytest

from cogency.core.config import Config
from cogency.core.stream import stream


@pytest.mark.asyncio
async def test_stream_orchestration():
    """Stream orchestrates mode selection, event processing, callbacks."""

    # Mock mode streams
    with (
        patch("cogency.core.stream.replay") as mock_replay,
        patch("cogency.core.stream.resume") as mock_resume,
    ):
        # Replay mode
        async def replay_events(*args):
            yield {"type": "respond", "content": "replay response"}

        mock_replay.stream = replay_events
        config = Config(llm=None, storage=None, tools=[], mode="replay")

        events = [e async for e in stream(config, "test", "user", "conv")]
        assert len(events) >= 1
        assert events[0]["content"] == "replay response"

        # Resume mode with fallback
        mock_resume.stream.side_effect = RuntimeError("WebSocket failed")
        config = Config(llm=None, storage=None, tools=[], mode="auto")  # auto mode enables fallback

        # Should fallback to replay
        events = [e async for e in stream(config, "test", "user", "conv")]
        assert len(events) >= 1
        assert events[0]["content"] == "replay response"

        # Callbacks invoked
        callback_called = False

        def test_callback(*args):
            nonlocal callback_called
            callback_called = True

        async for _ in stream(config, "test", "user", "conv", on_complete=test_callback):
            pass

        assert callback_called
