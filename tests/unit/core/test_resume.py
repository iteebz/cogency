"""Resume tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.core.config import Config
from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_resume_stream():
    """Resume stream requires WebSocket capability and handles completion detection."""

    # WebSocket not available - should reject
    mock_llm = Mock()
    mock_llm.resumable = False
    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=1)

    with pytest.raises(RuntimeError, match="Resume mode requires WebSocket support"):
        async for _ in resume_stream(config, "test", "user", "conv"):
            pass

    # WebSocket available - should connect and stream
    mock_llm.resumable = True
    mock_session = Mock()
    mock_llm.connect = AsyncMock(return_value=mock_session)
    mock_llm.close = AsyncMock()
    mock_llm.receive = AsyncMock()

    with (
        patch("cogency.core.resume.parse_stream") as mock_parse,
        patch("cogency.context.context.assemble") as mock_assemble,
        patch("cogency.lib.persist.persister") as mock_persister,
    ):
        # Mock context assembly
        mock_assemble.return_value = [{"role": "user", "content": "test"}]

        # Mock event persister
        mock_persister.return_value = AsyncMock()

        # Mock parse stream to return events with completion
        async def mock_events():
            yield {"type": "respond", "content": "response"}
            yield {"type": "end", "content": ""}

        mock_parse.return_value = mock_events()

        events = []
        async for event in resume_stream(config, "test", "user", "conv"):
            events.append(event)

        mock_llm.connect.assert_called_once()
        mock_llm.close.assert_called_once()
        assert len(events) == 2
        assert events[0]["type"] == "respond"
        assert events[1]["type"] == "end"
