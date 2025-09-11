"""Mode tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.core.config import Config
from cogency.core.protocols import Event
from cogency.core.replay import stream as replay_stream
from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_modes():
    """Modes handle streaming, iterations, tool execution, WebSocket capabilities."""

    # Replay mode - HTTP/stateless
    with (
        patch("cogency.core.replay.context") as mock_context,
        patch("cogency.core.replay.parse_stream") as mock_parse,
        patch("cogency.core.replay.execute") as mock_execute,
    ):
        mock_context.assemble.return_value = [{"role": "user", "content": "test"}]

        async def replay_events():
            yield {"type": Event.CALLS, "calls": [{"name": "tool"}]}
            yield {"type": Event.EXECUTE, "content": ""}
            yield {"type": Event.RESPOND, "content": "response"}

        mock_parse.return_value = replay_events()
        mock_execute.return_value = (["result"], {"type": "results"})

        config = Config(llm=Mock(), storage=Mock(), tools=[Mock()], max_iterations=2)
        events = []
        async for event in replay_stream(config, "test", "user", "conv"):
            events.append(event)
            if len(events) > 5:
                break

        assert mock_context.assemble.called
        assert mock_execute.called
        assert len(events) > 0

    # Resume mode - WebSocket/stateful
    mock_llm = Mock()
    mock_llm.resumable = True
    mock_session = Mock()
    mock_llm.connect = AsyncMock(return_value=mock_session)
    mock_llm.close = AsyncMock()

    from tests.conftest import mock_generator

    mock_llm.receive = Mock(side_effect=mock_generator(["token1", "token2"]))

    with (
        patch("cogency.core.resume.parse_stream") as mock_parse,
        patch("cogency.context.context.assemble") as mock_assemble,
        patch("cogency.lib.persist.persister") as mock_persister,
    ):

        async def resume_events():
            yield {"type": Event.RESPOND, "content": "websocket response"}
            yield {"type": Event.END, "content": ""}

        mock_parse.return_value = resume_events()
        mock_assemble.return_value = [{"role": "user", "content": "test"}]
        mock_persister.return_value = Mock()

        config = Config(llm=mock_llm, storage=Mock(), tools=[], max_iterations=1)
        events = []
        async for event in resume_stream(config, "test", "user", "conv"):
            events.append(event)

        mock_llm.connect.assert_called_once()
        assert len(events) == 2  # RESPOND + END
        assert events[0]["type"] == Event.RESPOND

    # Resume mode WebSocket validation
    mock_llm.resumable = False
    with pytest.raises(RuntimeError, match="Resume mode requires WebSocket support"):
        async for _ in resume_stream(config, "test", "user", "conv"):
            pass
