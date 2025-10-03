import asyncio
from unittest.mock import MagicMock, patch

import pytest

from cogency import Agent
from cogency.core.config import Security


def test_config(mock_llm, mock_storage):
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


def test_defaults(mock_llm, mock_storage):
    agent = Agent(llm=mock_llm, storage=mock_storage)
    assert agent.config.profile is False
    assert agent.config.security.access == "sandbox"
    assert agent.config.max_iterations > 0
    assert len(agent.config.tools) > 0
    assert hasattr(agent.config.llm, "generate")

    tool_names = {tool.name for tool in agent.config.tools}
    assert "file_list" in tool_names
    assert "recall" in tool_names


def test_custom_tools(mock_llm, mock_storage):
    mock_tool = MagicMock()
    mock_tool.name = "custom_tool"
    agent = Agent(llm=mock_llm, storage=mock_storage, tools=[mock_tool])
    assert len(agent.config.tools) == 1
    assert agent.config.tools[0].name == "custom_tool"


@pytest.mark.asyncio
async def test_fallback_learns(mock_llm, mock_storage):
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="auto", profile=True)

    with (
        patch("cogency.core.resume.stream") as mock_resume,
        patch("cogency.core.replay.stream") as mock_replay,
        patch("cogency.context.learn") as mock_learn,
    ):
        mock_resume.side_effect = Exception("WebSocket failed")

        async def mock_replay_stream(*args, **kwargs):
            yield {"type": "respond", "content": "test"}

        mock_replay.return_value = mock_replay_stream()

        events = [
            e async for e in agent("test query", user_id="test_user", conversation_id="test_convo")
        ]

        user_events = [e for e in events if e["type"] == "user"]
        assert len(user_events) == 1
        assert user_events[0]["content"] == "test query"

        mock_learn.assert_called_once()


@pytest.mark.asyncio
async def test_streaming(mock_llm, mock_storage):
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Test response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        response = None
        async for event in agent("Hello", user_id="test_user", conversation_id="test_convo"):
            if event["type"] == "respond":
                response = event["content"]
        assert response == "Test response"

        mock_stream.assert_called_once()
        call_args = mock_stream.call_args
        assert call_args.args[:3] == ("Hello", "test_user", "test_convo")
        assert call_args.kwargs["config"] is agent.config


@pytest.mark.asyncio
async def test_error_propagation(mock_llm, mock_storage):
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_failing_events():
            raise RuntimeError("Stream execution failed")
            yield

        mock_stream.return_value = mock_failing_events()

        with pytest.raises(RuntimeError, match="Stream execution failed"):
            async for _ in agent("Test query"):
                pass


@pytest.mark.asyncio
async def test_user_event_emission(mock_llm, mock_storage):
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        events = [
            e async for e in agent("Test query", user_id="test_user", conversation_id="conv_123")
        ]

        user_events = [e for e in events if e["type"] == "user"]
        assert len(user_events) == 1
        assert user_events[0]["content"] == "Test query"


@pytest.mark.asyncio
async def test_interrupt_persistence(mock_llm, mock_storage):
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_interrupted_events():
            yield {"type": "think", "content": "Thinking..."}
            raise KeyboardInterrupt()

        mock_stream.side_effect = lambda *args, **kwargs: mock_interrupted_events()

        events = []
        with pytest.raises(KeyboardInterrupt):
            async for event in agent(
                "Test query", user_id="test_user", conversation_id="test_conv"
            ):
                events.append(event)

        cancelled_events = [e for e in events if e["type"] == "cancelled"]
        assert len(cancelled_events) == 1
        assert cancelled_events[0]["content"] == "Task interrupted by user"

        cancelled_msgs = [m for m in mock_storage.messages if m["type"] == "cancelled"]
        assert len(cancelled_msgs) == 1
        assert cancelled_msgs[0]["conversation_id"] == "test_conv"
        assert cancelled_msgs[0]["user_id"] == "test_user"
        assert cancelled_msgs[0]["content"] == "Task interrupted by user"


@pytest.mark.asyncio
async def test_cancelled_error_persistence(mock_llm, mock_storage):
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.core.replay.stream") as mock_stream:

        async def mock_cancelled_events():
            yield {"type": "respond", "content": "Response"}
            raise asyncio.CancelledError()

        mock_stream.side_effect = lambda *args, **kwargs: mock_cancelled_events()

        events = []
        with pytest.raises(asyncio.CancelledError):
            async for event in agent(
                "Test query", user_id="test_user", conversation_id="test_conv"
            ):
                events.append(event)

        cancelled_events = [e for e in events if e["type"] == "cancelled"]
        assert len(cancelled_events) == 1

        cancelled_msgs = [m for m in mock_storage.messages if m["type"] == "cancelled"]
        assert len(cancelled_msgs) == 1
        assert cancelled_msgs[0]["conversation_id"] == "test_conv"
        assert cancelled_msgs[0]["user_id"] == "test_user"
        assert cancelled_msgs[0]["content"] == "Task interrupted by user"
