"""Continuous streaming tests."""

from unittest.mock import patch

import pytest

from cogency.core.agent import stream
from cogency.core.protocols import Event


@pytest.mark.asyncio
async def test_continuous_streaming():
    """Stream handles multiple RESPOND events and mode switching."""

    # Multiple responds followed by end
    async def mock_events():
        yield {"type": Event.RESPOND, "content": "Step 1"}
        yield {"type": Event.RESPOND, "content": "Step 2"}
        yield {"type": Event.RESPOND, "content": "Step 3"}
        yield {"type": Event.END, "content": ""}

    with patch("cogency.core.stream.replay") as mock_replay:
        mock_replay.stream = lambda *args: mock_events()

        from unittest.mock import Mock

        from cogency.core.config import Config

        config = Config(llm=Mock(), storage=Mock(), tools=[], mode="replay")

        events = []
        async for event in stream(config, "test", "user", "conv"):
            events.append(event)
            if event["type"] == Event.END:
                break

        respond_events = [e for e in events if e["type"] == Event.RESPOND]
        assert len(respond_events) == 3
        assert respond_events[0]["content"] == "Step 1"
        assert respond_events[1]["content"] == "Step 2"
        assert respond_events[2]["content"] == "Step 3"
        assert events[-1]["type"] == Event.END
