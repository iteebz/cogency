"""Agent orchestration tests: Verify Agent coordinates resume/replay/learn correctly.

These tests verify how Agent.__call__() handles:
- Fallback from resume (WebSocket) to replay (HTTP)
- Profile learning triggering
- Error propagation through streaming
- User event emission and interruption handling
"""

import asyncio
from unittest.mock import patch

import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_fallback_learns(mock_llm, mock_storage):
    """Auto mode falls back to replay and triggers learning on resume failure.

    Contract: When resume fails, fallback to replay and trigger profile learning.
    """
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="auto", profile=True)

    async def mock_replay_stream(*args, **kwargs):
        yield {"type": "respond", "content": "test"}

    with (
        patch("cogency.resume.stream") as mock_resume,
        patch("cogency.replay.stream") as mock_replay,
        patch("cogency.context.learn") as mock_learn,
    ):
        mock_resume.side_effect = RuntimeError("WebSocket failed")
        mock_replay.side_effect = mock_replay_stream

        events = [
            e async for e in agent("test query", user_id="test_user", conversation_id="test_convo")
        ]

        user_events = [e for e in events if e["type"] == "user"]
        assert len(user_events) == 1
        event = user_events[0]
        assert event["type"] == "user"
        content = event.get("content", "")
        assert content == "test query"

        mock_learn.assert_called_once()


@pytest.mark.asyncio
async def test_streaming(mock_llm, mock_storage):
    """Agent streams events through replay mode correctly.

    Contract: Agent passes query and parameters to underlying stream function.
    """
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Test response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        response = None
        async for event in agent("Hello", user_id="test_user", conversation_id="test_convo"):
            if event["type"] == "respond":
                response = event.get("content", "")
        assert response == "Test response"

        mock_stream.assert_called_once()
        call_args = mock_stream.call_args
        assert call_args.args[:3] == ("Hello", "test_user", "test_convo")
        assert call_args.kwargs["config"] is agent.config


@pytest.mark.asyncio
async def test_error_propagation(mock_llm, mock_storage):
    """Errors from stream propagate to caller as AgentError.

    Contract: Stream execution errors bubble up, not swallowed.
    """
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_failing_events():
            raise RuntimeError("Stream execution failed")
            yield

        mock_stream.return_value = mock_failing_events()

        from cogency.core.errors import LLMError

        with pytest.raises(LLMError, match="Stream execution failed"):
            async for _ in agent("Test query"):
                pass


@pytest.mark.asyncio
async def test_user_event_emission(mock_llm, mock_storage):
    """User event emitted as first event when agent is called.

    Contract: First event is always user event containing the query.
    """
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        events = [
            e async for e in agent("Test query", user_id="test_user", conversation_id="conv_123")
        ]

        user_events = [e for e in events if e["type"] == "user"]
        assert len(user_events) == 1
        event = user_events[0]
        assert event["type"] == "user"
        content = event.get("content", "")
        assert content == "Test query"


@pytest.mark.asyncio
async def test_interrupt_persistence(mock_llm, mock_storage):
    """KeyboardInterrupt yields cancelled event and ends stream cleanly.

    Contract: Interruption emits cancelled event, persists to storage, stream terminates.
    """
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_interrupted_events():
            yield {"type": "think", "content": "Thinking..."}
            raise KeyboardInterrupt()

        mock_stream.side_effect = lambda *args, **kwargs: mock_interrupted_events()

        events = [
            e async for e in agent("Test query", user_id="test_user", conversation_id="test_conv")
        ]

        cancelled_events = [e for e in events if e["type"] == "cancelled"]
        assert len(cancelled_events) == 1
        assert "timestamp" in cancelled_events[0]

        cancelled_msgs = [m for m in mock_storage.messages if m["type"] == "cancelled"]
        assert len(cancelled_msgs) == 1
        assert cancelled_msgs[0]["conversation_id"] == "test_conv"
        assert cancelled_msgs[0]["user_id"] == "test_user"


@pytest.mark.asyncio
async def test_cancelled_error_persistence(mock_llm, mock_storage):
    """asyncio.CancelledError yields cancelled event and ends stream cleanly.

    Contract: Task cancellation emits cancelled event, persists to storage, stream terminates.
    """
    agent = Agent(llm=mock_llm, storage=mock_storage, mode="replay")

    with patch("cogency.replay.stream") as mock_stream:

        async def mock_cancelled_events():
            yield {"type": "respond", "content": "Response"}
            raise asyncio.CancelledError()

        mock_stream.side_effect = lambda *args, **kwargs: mock_cancelled_events()

        events = [
            e async for e in agent("Test query", user_id="test_user", conversation_id="test_conv")
        ]

        cancelled_events = [e for e in events if e["type"] == "cancelled"]
        assert len(cancelled_events) == 1
        assert "timestamp" in cancelled_events[0]

        cancelled_msgs = [m for m in mock_storage.messages if m["type"] == "cancelled"]
        assert len(cancelled_msgs) == 1
        assert cancelled_msgs[0]["conversation_id"] == "test_conv"
        assert cancelled_msgs[0]["user_id"] == "test_user"
