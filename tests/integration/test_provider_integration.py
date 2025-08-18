"""Integration test for provider system with Agent."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.lib.result import Ok


@pytest.mark.asyncio
async def test_full_agent_provider_integration():
    """Test complete Agent integration with provider system."""
    # Mock provider
    mock_provider = Mock()
    mock_provider.generate = AsyncMock(return_value=Ok("Hello from provider"))

    with patch("cogency.core.agent.create_llm", return_value=mock_provider):
        with patch("cogency.core.agent.context", return_value="test context"):
            from cogency.core.agent import Agent

            # Create agent with string shortcut
            agent = Agent(llm="claude", tools=[], max_iterations=1)

            # Execute with runtime user_id
            result = await agent("Test query", user_id="integration_test")

    # Verify result
    assert result.response == "Hello from provider"
    assert "integration_test" in result.conversation_id

    # Verify provider called correctly
    mock_provider.generate.assert_called_once()
    call_args = mock_provider.generate.call_args[0][0]  # First positional arg
    assert len(call_args) == 1  # Single message
    assert call_args[0]["role"] == "user"
    assert "Test query" in call_args[0]["content"]


def test_backward_compatibility_preserved():
    """Ensure existing Agent() call still works."""
    with patch("cogency.core.agent.create_llm") as mock_create:
        mock_create.return_value = Mock()
        from cogency.core.agent import Agent

        # This should work without errors
        agent = Agent()
        assert agent is not None

        # Should default to OpenAI
        mock_create.assert_called_with("openai")
