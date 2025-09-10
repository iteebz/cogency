"""Integration test for continuous agent streaming with multiple RESPOND events."""

from unittest.mock import Mock, patch

import pytest

from cogency import Agent
from cogency.core.protocols import Event


@pytest.mark.asyncio
async def test_http_continuous_streaming():
    """Test HTTP mode supports multiple RESPOND events."""

    # Mock LLM that streams multiple RESPOND events
    async def mock_continuous_stream(*args):
        """Mock continuous streaming with multiple responses."""
        tokens = [
            "Starting the task...",
            "§RESPOND",
            "Step 1: Setting up environment",
            "§RESPOND",
            "Step 2: Processing data",
            "§RESPOND",
            "Step 3: Generating output",
            "§END",
        ]
        for token in tokens:
            yield token

    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = Mock()
        mock_llm.stream = Mock(return_value=mock_continuous_stream())
        mock_llm.resumable = False  # Force HTTP mode
        mock_gemini.return_value = mock_llm

        agent = Agent(mode="replay", llm="gemini")

        # Collect all streaming events
        events = []
        async for event in agent.stream("Do a multi-step task"):
            events.append(event)
            if event["type"] == Event.END:
                break

        # Should get multiple RESPOND events
        respond_events = [e for e in events if e["type"] == Event.RESPOND]
        assert (
            len(respond_events) >= 3
        ), f"Expected multiple RESPOND events, got {len(respond_events)}"

        # Verify content progression
        assert "Step 1" in respond_events[0]["content"]
        assert "Step 2" in respond_events[1]["content"]
        assert "Step 3" in respond_events[2]["content"]

        # Should end with END event
        assert events[-1]["type"] == Event.END


@pytest.mark.asyncio
async def test_websocket_continuous_streaming():
    """Test WebSocket mode supports multiple RESPOND events."""

    from cogency.core.protocols import WebSocketSession
    from tests.conftest import mock_generator

    # Mock WebSocket tokens for continuous streaming
    websocket_tokens = [
        "Analyzing request...",
        "§RESPOND",
        "Phase 1: Initial analysis complete",
        "§RESPOND",
        "Phase 2: Data processing in progress",
        "§RESPOND",
        "Phase 3: Finalizing results",
        "§YIELD",  # Proper completion signal for WebSocket
    ]

    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = Mock()
        mock_llm.resumable = True  # Enable WebSocket

        # Mock connect as async function returning WebSocket session
        async def mock_connect(*args):
            return WebSocketSession(session=Mock(), connection=Mock(), types=Mock())

        mock_llm.connect = Mock(side_effect=mock_connect)
        mock_llm.receive = Mock(side_effect=mock_generator(websocket_tokens))

        # Mock close as async function
        async def mock_close(*args):
            return True

        mock_llm.close = Mock(side_effect=mock_close)

        mock_gemini.return_value = mock_llm

        agent = Agent(mode="resume", llm="gemini")

        # Collect all streaming events
        events = []
        async for event in agent.stream("Do a multi-phase analysis"):
            events.append(event)
            if event["type"] == Event.YIELD:
                break  # WebSocket completes with YIELD

        # Should get multiple RESPOND events
        respond_events = [e for e in events if e["type"] == Event.RESPOND]
        assert (
            len(respond_events) >= 3
        ), f"Expected multiple RESPOND events, got {len(respond_events)}"

        # Verify content progression
        assert "Phase 1" in respond_events[0]["content"]
        assert "Phase 2" in respond_events[1]["content"]
        assert "Phase 3" in respond_events[2]["content"]

        # Should end with YIELD event
        assert events[-1]["type"] == Event.YIELD

        # NOTE: close() may not be called if test breaks early
        # The key test is that continuous streaming works with multiple RESPOND events


@pytest.mark.asyncio
async def test_unified_interface():
    """Test that both modes provide identical streaming interface."""

    from cogency.core.protocols import WebSocketSession
    from tests.conftest import mock_generator

    # Same token stream for both modes
    tokens = ["Working on task", "§RESPOND", "Task complete", "§END"]

    results_http = []
    results_ws = []

    # Test HTTP mode
    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = Mock()
        mock_llm.stream = Mock(side_effect=mock_generator(tokens))
        mock_llm.resumable = False
        mock_gemini.return_value = mock_llm

        agent_http = Agent(mode="replay", llm="gemini")
        async for event in agent_http.stream("Test task"):
            results_http.append((event["type"], len(event["content"])))
            if event["type"] == Event.END:
                break

    # Test WebSocket mode
    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = Mock()
        mock_llm.resumable = True

        # Mock connect as async function returning WebSocket session
        async def mock_connect(*args):
            return WebSocketSession(session=Mock(), connection=Mock(), types=Mock())

        mock_llm.connect = Mock(side_effect=mock_connect)
        mock_llm.receive = Mock(side_effect=mock_generator(tokens))

        # Mock close as async function
        async def mock_close(*args):
            return True

        mock_llm.close = Mock(side_effect=mock_close)

        mock_gemini.return_value = mock_llm

        agent_ws = Agent(mode="resume", llm="gemini")
        async for event in agent_ws.stream("Test task"):
            results_ws.append((event["type"], len(event["content"])))
            if event["type"] == Event.END:
                break

    # Both modes should produce identical event streams
    assert len(results_http) == len(results_ws), "Event count should match"

    # Event types should be identical
    http_types = [r[0] for r in results_http]
    ws_types = [r[0] for r in results_ws]
    assert http_types == ws_types, "Event types should be identical"
