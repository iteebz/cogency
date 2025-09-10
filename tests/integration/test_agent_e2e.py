"""Integration tests - First principles V3 launch coverage."""

from unittest.mock import Mock, patch

import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_agent_basic_response():
    from tests.conftest import mock_llm_stream

    """Agent produces response end-to-end."""

    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = mock_llm_stream()
        mock_gemini.return_value = mock_llm

        agent = Agent(mode="replay", llm="gemini")

        response = await agent("Hello")

        # Should get string response
        assert isinstance(response, str)
        assert len(response) > 0

        # HTTP replay mode: NEVER calls connect(), calls stream() at least once
        assert mock_llm.stream.call_count >= 1  # May iterate multiple times now
        assert mock_llm.connect.call_count == 0  # HTTP is stateless


@pytest.mark.asyncio
async def test_agent_with_delimiters():
    from tests.conftest import mock_llm_stream

    """Agent handles delimiter parsing."""

    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = mock_llm_stream()
        mock_gemini.return_value = mock_llm

        agent = Agent(mode="replay", llm="gemini")

        response = await agent("Hello")

        # Should get clean response
        assert isinstance(response, str)
        assert len(response) > 0

        # Should not contain delimiters in final response
        assert "§" not in response


@pytest.mark.asyncio
async def test_agent_error_handling():
    from tests.conftest import mock_llm_stream

    """Agent handles errors gracefully."""

    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = mock_llm_stream()

        # Mock stream failure (HTTP mode uses stream(), not connect())
        class MockAsyncIterator:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise Exception("Test stream error")

        mock_llm.stream = Mock(return_value=MockAsyncIterator())

        mock_gemini.return_value = mock_llm

        agent = Agent(mode="replay", llm="gemini")

        # Should raise controlled error with helpful message
        with pytest.raises(RuntimeError) as exc_info:
            await agent("Hello")

        assert "Agent execution failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_agent_user_isolation():
    from tests.conftest import mock_llm_stream

    """Agent maintains user isolation."""

    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = mock_llm_stream()
        mock_gemini.return_value = mock_llm

        agent = Agent(mode="replay", llm="gemini")

        # Different users should work independently
        response1 = await agent("Hello", user_id="user1")
        response2 = await agent("Hello", user_id="user2")

        assert isinstance(response1, str)
        assert isinstance(response2, str)

        # HTTP replay mode: NEVER calls connect(), calls stream() for each user
        assert mock_llm.stream.call_count >= 2  # May iterate multiple times per user
        assert mock_llm.connect.call_count == 0  # HTTP is stateless


@pytest.mark.asyncio
async def test_agent_websocket_mode():
    from cogency.core.protocols import WebSocketSession
    from tests.conftest import mock_llm_stream

    """Agent WebSocket mode calls connect(), not stream()."""

    with patch("cogency.lib.llms.Gemini") as mock_gemini:
        mock_llm = mock_llm_stream()

        # Mock WebSocket session
        mock_session = WebSocketSession(session=Mock(), connection=Mock(), types=Mock())
        mock_llm.connect.return_value = mock_session
        mock_llm.resumable = True  # Enable WebSocket capability

        # Mock receive to yield tokens
        async def mock_receive(*args):
            yield "§RESPOND"
            yield "Test response"
            yield "§YIELD"

        mock_llm.receive = Mock(side_effect=mock_receive)
        mock_gemini.return_value = mock_llm

        agent = Agent(mode="resume", llm="gemini")

        response = await agent("Hello")

        # Should get string response
        assert isinstance(response, str)
        assert len(response) > 0

        # WebSocket mode: ALWAYS calls connect(), NEVER calls stream()
        mock_llm.connect.assert_called_once()
        assert mock_llm.stream.call_count == 0  # WebSocket doesn't use stream()
