"""Test Agent with provider system integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.fixture
def mock_llm():
    """Mock LLM provider."""
    llm = Mock()
    llm.generate = AsyncMock()
    return llm


@pytest.mark.asyncio
async def test_agent_with_llm_provider(mock_llm):
    """Agent uses configured LLM provider."""
    from cogency.lib.result import Ok

    # Mock LLM response
    mock_llm.generate.return_value = Ok("Hello world")

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        from cogency.core.agent import Agent

        agent = Agent(llm="claude", tools=[])
        result = await agent("Hello", user_id="test")

    assert result.response == "Hello world"
    mock_llm.generate.assert_called_once()


def test_agent_default_provider():
    """Agent defaults to OpenAI provider."""

    with patch("cogency.core.agent.create_llm") as mock_create:
        mock_create.return_value = Mock()
        from cogency.core.agent import Agent

        Agent()

    mock_create.assert_called_once_with("openai")


@pytest.mark.asyncio
async def test_agent_runtime_user_id(mock_llm):
    """Agent passes runtime user_id to context."""
    from cogency.lib.result import Ok

    mock_llm.generate.return_value = Ok("Response")

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        with patch("cogency.core.agent.context") as mock_context:
            mock_context.return_value = "context"

            from cogency.core.agent import Agent

            agent = Agent(tools=[])
            await agent("Query", user_id="alice")

    # Verify context called with runtime user_id
    mock_context.assert_called_with("Query", "alice", [])
