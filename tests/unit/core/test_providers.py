"""Test Agent with provider system integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.asyncio
async def test_agent_with_llm_provider(mock_llm):
    """Agent uses configured LLM provider."""
    from cogency.lib.result import Ok

    # Mock LLM response
    xml_response = """<thinking>
User said hello.
</thinking>

<response>
Hello world
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        from cogency.core.agent import Agent

        agent = Agent(llm="claude", tools=[])
        result = await agent("Hello", user_id="test")

    assert "Hello world" in result.response
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

    xml_response = """<thinking>
Processing query.
</thinking>

<response>
Response
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        with patch("cogency.core.react.context") as mock_context:
            mock_context.assemble.return_value = "context"

            from cogency.core.agent import Agent

            agent = Agent(tools=[])
            await agent("Query", user_id="alice")

    # Verify context called with runtime user_id
    call_args = mock_context.assemble.call_args[0]
    assert call_args[0] == "Query"
    assert call_args[1] == "alice"
    assert call_args[2].startswith("alice_")  # conversation_id
    assert (
        len(call_args) == 6
    )  # 6 parameter signature (query, user_id, conversation_id, task_id, tools, iteration)
