"""Agent configuration and execution tests."""

from unittest.mock import MagicMock, patch

import pytest

from cogency import Agent
from cogency.core.config import Security


def test_config(mock_llm, mock_storage):
    """Agent handles configuration, defaults, tools, and providers correctly."""
    # Custom config
    agent = Agent(
        llm="gemini",
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

    # Defaults
    agent = Agent(llm=mock_llm, storage=mock_storage)
    assert agent.config.profile is True
    assert agent.config.security.access == "sandbox"
    assert agent.config.max_iterations > 0
    assert len(agent.config.tools) > 0
    assert hasattr(agent.config.llm, "generate")

    tool_names = {tool.name for tool in agent.config.tools}
    assert "file_list" in tool_names
    assert "recall" in tool_names


@pytest.mark.asyncio
async def test_auto_mode_profile_learning(mock_config, mock_llm, mock_storage):
    """Test that auto mode triggers profile learning when falling back to replay."""
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="auto")

    # Mock resume.stream to fail, triggering fallback
    with (
        patch("cogency.core.resume.stream") as mock_resume,
        patch("cogency.core.replay.stream") as mock_replay,
        patch("cogency.context.learn") as mock_learn,
    ):
        # Make resume fail to trigger fallback
        mock_resume.side_effect = Exception("WebSocket failed")

        async def mock_replay_stream(*args, **kwargs):
            yield {"type": "respond", "content": "test"}

        mock_replay.return_value = mock_replay_stream()

        # Execute agent
        events = []
        async for event in agent("test query", user_id="test_user"):
            events.append(event)

        # Verify storage received user message
        messages = await mock_storage.load_messages("test_user")
        user_messages = [m for m in messages if m["type"] == "user"]
        assert len(user_messages) > 0, "Agent must save user message to storage"
        assert any("test query" in m["content"] for m in user_messages)

        # Verify learning was called (part of finalization)
        mock_learn.assert_called_once()

    # Custom tools
    mock_tool = MagicMock()
    mock_tool.name = "custom_tool"
    agent = Agent(llm=mock_llm, storage=mock_storage, tools=[mock_tool])
    assert len(agent.config.tools) == 1
    assert agent.config.tools[0].name == "custom_tool"


@pytest.mark.asyncio
async def test_execution(mock_llm, mock_storage):
    """Agent executes with proper streaming, context, and error handling."""
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Test response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        response = None
        async for event in agent("Hello", user_id="test_user"):
            if event["type"] == "respond":
                response = event["content"]
        assert response == "Test response"

        mock_stream.assert_called_once()
        call_args = mock_stream.call_args
        assert call_args.args[:3] == ("Hello", "test_user", "test_user")
        assert call_args.kwargs["config"] is agent.config

    # Error handling
    error_agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_failing_events():
            raise RuntimeError("Stream execution failed")
            yield

        mock_stream.return_value = mock_failing_events()

        with pytest.raises(RuntimeError, match="Stream execution failed"):
            async for _ in error_agent("Test query"):
                pass

    # Empty response should just stream events as-is
    empty_agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_empty_events():
            yield {"type": "think", "content": "Just thinking"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_empty_events()

        events = []
        async for event in empty_agent("Test query"):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == "think"


@pytest.mark.asyncio
async def test_user_message_persistence(mock_llm, mock_storage):
    """Agent persists user messages for conversation context."""
    from unittest.mock import AsyncMock

    # Mock the save_message method to track calls
    mock_storage.save_message = AsyncMock()
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        # Execute agent call
        async for _ in agent("Test query", user_id="test_user", conversation_id="conv_123"):
            pass

        # Verify user message was persisted
        mock_storage.save_message.assert_called_with("conv_123", "test_user", "user", "Test query")
