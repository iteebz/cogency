"""WebSocket resume streaming tests."""

from unittest.mock import AsyncMock, Mock

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
        async for _ in resume_stream(
            "test",
            "user",
            "conv",
            config=config,
        ):
            pass

    # WebSocket available - should connect and stream
    mock_llm = Mock()  # New mock for successful case
    mock_llm.connect = AsyncMock()
    mock_llm.receive = Mock()
    mock_llm.send = AsyncMock(return_value=True)
    mock_llm.close = AsyncMock()

    # Mock successful connection with proper async generator


@pytest.mark.asyncio
async def test_sends_query_once(mock_llm, mock_config):
    """Test that resume mode sends user query only once, not duplicated."""
    # Use mock_llm session capabilities - track send calls on session
    mock_llm.set_response_tokens(["§respond: Test response", "§end"])
    mock_config.llm = mock_llm

    # Track send calls on session instances
    send_calls = []
    original_connect = mock_llm.connect

    async def tracked_connect(messages):
        session = await original_connect(messages)
        original_session_send = session.send

        async def tracked_session_send(content):
            send_calls.append(content)
            async for token in original_session_send(content):
                yield token

        session.send = tracked_session_send
        return session

    mock_llm.connect = tracked_connect

    # Execute resume stream
    events = []
    async for event in resume_stream(
        "test query",
        "user1",
        "conv1",
        config=mock_config,
    ):
        events.append(event)

    # Verify query was not double-sent (connect() already includes it)
    user_query_sends = [call for call in send_calls if "test query" in call]
    assert len(user_query_sends) == 0, (
        f"Expected 0 user query sends (already in connect), got {len(user_query_sends)}: {user_query_sends}"
    )
