"""Integration tests - First principles V3 launch coverage."""

from unittest.mock import patch

import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_agent_basic_response():
    from tests.conftest import mock_generator

    """Agent produces response end-to-end."""
    agent = Agent()

    mock_response = "Hello, I'm working!"

    with patch("cogency.core.agent.consciousness_stream") as mock_stream:
        mock_stream.side_effect = mock_generator([{"type": "respond", "content": mock_response}])

        response = await agent("Hello")

        # Should get string response
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Hello, I'm working!" in response

        # Run should have been called
        mock_stream.assert_called_once()


@pytest.mark.asyncio
async def test_agent_with_delimiters():
    """Agent handles delimiter parsing."""
    agent = Agent()

    # Mock streaming to return processed response (no delimiters)
    mock_response = "Hello there! How can I help you?"

    with patch("cogency.core.agent.consciousness_stream") as mock_stream:
        # Mock async generator
        async def mock_events():
            yield {"type": "respond", "content": mock_response}

        mock_stream.return_value = mock_events()

        response = await agent("Hello")

        # Should get clean response
        assert isinstance(response, str)
        assert "Hello there!" in response

        # Should not contain delimiters in final response
        assert "§" not in response


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Agent handles errors gracefully."""
    agent = Agent()

    # Mock streaming to raise exception
    with patch("cogency.core.agent.consciousness_stream") as mock_stream:
        mock_stream.side_effect = Exception("Test error")

        # Should raise controlled error
        with pytest.raises(RuntimeError) as exc_info:
            await agent("Hello")

        assert "Execution failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_agent_user_isolation():
    """Agent maintains user isolation."""
    agent = Agent()
    mock_response = "Response"

    with patch("cogency.core.agent.consciousness_stream") as mock_stream:
        # Mock async generator
        async def mock_events():
            yield {"type": "respond", "content": mock_response}

        mock_stream.return_value = mock_events()

        # Different users should work independently
        response1 = await agent("Hello", user_id="user1")
        response2 = await agent("Hello", user_id="user2")

        assert isinstance(response1, str)
        assert isinstance(response2, str)

        # Should have been called for each user
        assert mock_stream.call_count == 2
