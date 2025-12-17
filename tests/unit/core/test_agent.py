"""Unit tests for Agent configuration and parameter handling.

These tests verify Agent initialization and parameter passing.
Full integration tests (orchestration, streaming, errors) are in
tests/integration/test_agent_orchestration.py
"""

from unittest.mock import MagicMock, patch

import pytest

from cogency import Agent
from cogency.core.config import Security


def test_config(mock_llm, mock_storage):
    """Agent accepts custom configuration and stores it."""
    agent = Agent(
        llm=mock_llm,
        storage=mock_storage,
        tools=[],
        profile=False,
        security=Security(access="system"),
        max_iterations=5,
    )
    assert agent.config.profile is False
    assert agent.config.security.access == "system"
    assert agent.config.max_iterations == 5
    assert len(agent.config.tools) == 0


def test_defaults(mock_llm, mock_storage):
    """Agent uses correct defaults when not specified."""
    agent = Agent(llm=mock_llm, storage=mock_storage)
    assert agent.config.profile is False
    assert agent.config.security.access == "sandbox"
    assert agent.config.max_iterations > 0
    assert len(agent.config.tools) > 0
    assert hasattr(agent.config.llm, "generate")

    tool_names = {tool.name for tool in agent.config.tools}
    assert "write" in tool_names
    assert "recall" in tool_names


def test_custom_tools(mock_llm, mock_storage):
    """Agent accepts custom tool list."""
    mock_tool = MagicMock()
    mock_tool.name = "custom_tool"
    agent = Agent(llm=mock_llm, storage=mock_storage, tools=[mock_tool])
    assert len(agent.config.tools) == 1
    assert agent.config.tools[0].name == "custom_tool"


@pytest.mark.asyncio
async def test_stream_event_default(mock_llm, mock_storage):
    """stream='event' is default behavior."""
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Test"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        async for _ in agent("Test"):
            pass

        mock_stream.assert_called_once()
        call_kwargs = mock_stream.call_args.kwargs
        assert call_kwargs["stream"] == "event"


@pytest.mark.asyncio
async def test_stream_token_parameter(mock_llm, mock_storage):
    """stream='token' passes to underlying stream function."""
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Test"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        async for _ in agent("Test", stream="token"):
            pass

        call_kwargs = mock_stream.call_args.kwargs
        assert call_kwargs["stream"] == "token"


@pytest.mark.asyncio
async def test_stream_none_parameter(mock_llm, mock_storage):
    """stream=None passes to underlying stream function."""
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Test"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        async for _ in agent("Test", stream=None):
            pass

        call_kwargs = mock_stream.call_args.kwargs
        assert call_kwargs["stream"] is None
