"""Integration test for provider system with Agent."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.lib.result import Ok


@pytest.mark.asyncio
async def test_full_agent_provider_integration(mock_llm):
    """Test complete Agent integration with provider system."""
    # Use canonical mock fixture
    xml_response = """<thinking>
Processing integration test.
</thinking>

<response>
Hello from provider
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        with patch(
            "cogency.core.react.context.assemble",
            return_value=[{"role": "user", "content": "Test query"}],
        ):
            from cogency.core.agent import Agent

            # Create agent with string shortcut
            agent = Agent(llm="claude", tools=[], max_iterations=1)

            # Execute with runtime user_id
            result = await agent("Test query", user_id="integration_test")

    # Verify result
    assert "Hello from provider" in result.response
    assert "integration_test" in result.conversation_id

    # Verify provider called correctly
    mock_llm.generate.assert_called_once()
    call_args = mock_llm.generate.call_args[0][0]  # First positional arg
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
