"""Mode tests - Replay vs Inject execution patterns."""

from unittest.mock import Mock, patch

import pytest

from cogency.core.config import Config
from cogency.core.protocols import Event
from cogency.core.replay import stream as replay_stream
from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_replay_stateless_behavior():
    from tests.conftest import mock_generator, mock_llm_stream

    """Replay rebuilds context every iteration - stateless."""
    mock_llm = mock_llm_stream()

    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=2)

    with patch("cogency.core.replay.context") as mock_context:
        mock_context.assemble.return_value = [{"role": "user", "content": "test"}]

        with patch("cogency.core.replay.parse_stream") as mock_parse:
            # Use async generator factory to prevent hanging
            mock_parse.side_effect = mock_generator(
                [{"type": Event.RESPOND, "content": "done"}, {"type": "end"}]
            )

            events = []
            async for event in replay_stream(config, "test query", "user", "conv"):
                events.append(event)

            # Should call context.assemble for each iteration
            assert mock_context.assemble.called
            assert len(events) >= 1


@pytest.mark.asyncio
async def test_replay_max_iterations():
    from tests.conftest import mock_generator, mock_llm_stream

    """Replay respects max_iterations limit."""
    mock_llm = mock_llm_stream()

    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=2)

    with patch("cogency.core.replay.context") as mock_context:
        mock_context.assemble.return_value = [{"role": "user", "content": "test"}]

        with patch("cogency.core.replay.parse_stream") as mock_parse:
            # Use async generator factory to prevent hanging
            mock_parse.side_effect = mock_generator(
                [
                    {"type": Event.CALLS, "calls": [{"name": "test"}]},
                    {"type": "wait"},
                    {"type": Event.CALLS, "calls": [{"name": "test"}]},
                    {"type": "wait"},
                    {"type": Event.RESPOND, "content": "max iterations reached"},
                ]
            )

            # Should terminate after max_iterations, not run forever
            events = []
            async for event in replay_stream(config, "test", "user", "conv"):
                events.append(event)
                if len(events) > 10:  # Safety break
                    break

            # Should respect iteration limit
            assert len(events) <= 10  # Terminated, not infinite


@pytest.mark.asyncio
async def test_inject_stateful_behavior(mock_llm, mock_storage):
    """Inject maintains WebSocket session state."""
    # Use fixture with proper async generator support
    from tests.conftest import mock_generator

    mock_llm.resumable = True
    mock_llm.stream = Mock(side_effect=lambda *args: mock_generator(["stream_token"])())

    # Override with custom tokens for this test

    mock_llm.receive.side_effect = mock_generator(["token1", "token2"])

    config = Config(llm=mock_llm, storage=mock_storage, tools=[], max_iterations=2)

    with patch("cogency.context") as mock_context:
        mock_context.assemble.return_value = [{"role": "user", "content": "test"}]

        with patch("cogency.core.resume.parse_stream") as mock_parse:

            async def mock_events():
                yield {"type": Event.RESPOND, "content": "websocket response"}
                yield {"type": Event.YIELD, "content": "complete"}

            mock_parse.return_value = mock_events()

            events = []
            async for event in resume_stream(config, "test", "user", "conv"):
                events.append(event)

            # Should establish WebSocket session and complete successfully
            mock_llm.connect.assert_called_once()
            assert len(events) >= 1


@pytest.mark.asyncio
async def test_inject_websocket_fallback():
    from tests.conftest import mock_llm_stream

    """Resume mode properly rejects when WebSocket unavailable."""
    mock_llm = mock_llm_stream()
    mock_llm.resumable = False  # No WebSocket capability

    config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=2)

    # Resume mode should fail when WebSocket not available
    with pytest.raises(RuntimeError, match="Resume mode requires WebSocket support"):
        async for _event in resume_stream(config, "test", "user", "conv"):
            pass  # Should not reach here


@pytest.mark.asyncio
async def test_mode_tool_execution():
    from tests.conftest import mock_generator, mock_llm_stream

    """Both modes execute tools and inject results."""
    mock_llm = mock_llm_stream()
    mock_tool = Mock()
    mock_tool.name = "test_tool"

    config = Config(llm=mock_llm, storage=Mock(), tools=[mock_tool], max_iterations=1)

    with patch("cogency.core.replay.context") as mock_context:
        mock_context.assemble.return_value = [{"role": "user", "content": "test"}]

        with patch("cogency.core.replay.parse_stream") as mock_parse:
            # Use async generator factory to prevent hanging
            mock_parse.side_effect = mock_generator(
                [
                    {"type": Event.CALLS, "calls": [{"name": "test_tool", "args": {}}]},
                    {"type": Event.YIELD, "content": "execute"},  # This triggers tool execution
                    {"type": Event.RESPOND, "content": "after tools"},
                    {"type": "end"},
                ]
            )

            with patch("cogency.core.execute.execute_tools_and_save") as mock_execute:
                mock_execute.return_value = (
                    ["tool result"],
                    {"type": "results", "content": "test"},
                )

                events = []
                async for event in replay_stream(config, "test", "user", "conv"):
                    events.append(event)

                # Should execute tools when encountered
                mock_execute.assert_called_once()


def test_mode_functions_exist():
    """Mode functions match mental model naming."""
    # replay = HTTP/stateless
    # inject = WebSocket/stateful
    assert callable(replay_stream)
    assert callable(resume_stream)

    # Mode module was purged - functions are now in separate files
    # replay = core.replay.py (HTTP/stateless)
    # inject = core.inject.py (WebSocket/stateful)
    pass
