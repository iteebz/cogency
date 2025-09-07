"""Streaming integration tests - transport mechanics."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_agent_http_mode():
    """Agent uses HTTP mode correctly."""
    from cogency import Agent

    agent = Agent(mode="replay")  # Test basic mode functionality

    with patch("cogency.core.agent.stream") as mock_stream:
        # Mock async generator
        async def mock_events():
            yield {"type": "respond", "content": "HTTP response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        result = await agent("Test query")

        assert result == "HTTP response"
        mock_stream.assert_called_once()

        # Verify stream was passed correctly
        call_args = mock_stream.call_args[0][0]  # First arg is config
        assert call_args.mode == "replay"


@pytest.mark.asyncio
async def test_agent_websocket_mode():
    """Agent uses WebSocket mode correctly."""
    from cogency import Agent

    agent = Agent(mode="resume")  # Test resume mode functionality

    with patch("cogency.core.agent.stream") as mock_stream:
        # Mock async generator
        async def mock_events():
            yield {"type": "respond", "content": "WebSocket response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        result = await agent("Test query")

        assert result == "WebSocket response"
        mock_stream.assert_called_once()

        # Verify stream was passed
        call_args = mock_stream.call_args[0][0]
        assert call_args.mode == "resume"


@pytest.mark.asyncio
async def test_agent_auto_mode():
    """Agent auto mode selects transport correctly."""
    from cogency import Agent

    agent = Agent(mode="auto")  # Test auto mode functionality

    with patch("cogency.core.agent.stream") as mock_stream:
        # Mock async generator
        async def mock_events():
            yield {"type": "respond", "content": "Auto mode response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        result = await agent("Test query")

        assert result == "Auto mode response"
        mock_stream.assert_called_once()

        # Verify auto mode was passed
        call_args = mock_stream.call_args[0][0]
        assert call_args.mode == "auto"
