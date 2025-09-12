"""Resume tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.core.config import Config
from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_resume_stream():
    """Resume stream requires WebSocket capability and handles completion detection."""

    # WebSocket not available - should reject (no connect method)
    mock_llm = Mock(spec=[])  # Empty spec means no methods
    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=1)

    with pytest.raises(RuntimeError, match="Resume mode requires WebSocket support"):
        async for _ in resume_stream(config, "test", "user", "conv"):
            pass

    # WebSocket available - should connect and stream
    mock_llm = Mock()  # New mock for successful case
    mock_llm.connect = AsyncMock()
    mock_llm.receive = Mock()
    mock_llm.send = AsyncMock(return_value=True)
    mock_llm.close = AsyncMock()

    # Mock successful connection
    mock_session = Mock()
    mock_llm.connect.return_value = mock_session
    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=1)

    with (
        patch("cogency.core.resume.Accumulator") as mock_accumulator,
        patch("cogency.context.context.assemble") as mock_assemble,
        patch("cogency.core.resume.parse_tokens") as mock_parse,
    ):
        # Mock context assembly
        mock_assemble.return_value = [{"role": "user", "content": "test"}]

        # Mock token stream
        async def mock_token_stream():
            yield "response"

        mock_llm.receive.return_value = mock_token_stream()

        # Mock parser events
        async def mock_parser_events():
            yield {"type": "respond", "content": "response"}
            yield {"type": "end", "content": ""}

        mock_parse.return_value = mock_parser_events()

        # Mock accumulator to return events
        async def mock_accumulator_events():
            yield {"type": "respond", "content": "response"}
            yield {"type": "end", "content": ""}

        mock_acc_instance = Mock()
        mock_acc_instance.process = Mock(return_value=mock_accumulator_events())
        mock_accumulator.return_value = mock_acc_instance

        events = []
        async for event in resume_stream(config, "test", "user", "conv"):
            events.append(event)

        mock_llm.connect.assert_called_once()
        assert len(events) == 2
        assert events[0]["type"] == "respond"
        assert events[1]["type"] == "end"
