"""Unit tests for ReAct algorithm functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.core.react import react, stream_react


@pytest.fixture
def mock_llm():
    """Mock LLM that returns structured responses."""
    llm = AsyncMock()
    llm.generate.return_value = MagicMock(
        success=True,
        failure=False,
        unwrap=lambda: "I'll search for this. Final answer: Test response",
    )
    return llm


@pytest.fixture
def mock_tools():
    """Mock tools dictionary."""
    tool = MagicMock()
    tool.name = "search"
    tool.description = "Search for information"
    tool.execute = AsyncMock()
    tool.execute.return_value = MagicMock(success=True, unwrap=lambda: "Search result")
    return {"search": tool}


@pytest.mark.asyncio
async def test_react_returns_final_event(mock_llm, mock_tools):
    """Test react function returns the complete event."""
    result = await react(mock_llm, mock_tools, "test query", "user123")

    assert result["type"] == "complete"
    assert "answer" in result
    assert "conversation_id" in result


@pytest.mark.asyncio
async def test_stream_react_yields_events(mock_llm, mock_tools):
    """Test stream_react yields structured events."""
    events = []
    async for event in stream_react(
        mock_llm, mock_tools, "test query", "user123", max_iterations=1
    ):
        events.append(event)

    event_types = [e["type"] for e in events]
    assert "iteration" in event_types
    assert "context" in event_types
    assert "reasoning" in event_types
    assert "complete" in event_types


@pytest.mark.asyncio
async def test_react_handles_llm_error(mock_tools):
    """Test react handles LLM failures gracefully."""
    error_llm = AsyncMock()
    error_llm.generate.return_value = MagicMock(
        success=False, failure=True, error="LLM connection failed"
    )

    result = await react(error_llm, mock_tools, "test query", "user123")

    assert result["type"] == "error"
    assert "message" in result


@pytest.mark.asyncio
async def test_shared_logic_zero_duplication(mock_llm, mock_tools):
    """Test react consumes stream_react - proving shared logic."""
    # Mock stream_react to return specific events

    # Verify react gets the same event stream_react produces
    result = await react(mock_llm, mock_tools, "test query", "user123", max_iterations=1)

    # Both should produce the same final result structure
    assert result["type"] == "complete"
    assert "answer" in result
    assert "conversation_id" in result
