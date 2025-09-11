"""Agent tests."""

from unittest.mock import MagicMock, patch

import pytest

from cogency import Agent
from cogency.core.config import Config


def test_config():
    """Agent handles configuration, defaults, tools, and providers correctly."""
    # Custom config
    agent = Agent(llm="gemini", tools=[], profile=False, sandbox=False, max_iterations=5)
    assert agent.config.profile is False
    assert agent.config.sandbox is False
    assert agent.config.max_iterations == 5
    assert len(agent.config.tools) == 0

    # Defaults
    agent = Agent()
    assert agent.config.profile is True
    assert agent.config.sandbox is True
    assert agent.config.max_iterations > 0
    assert len(agent.config.tools) > 0
    assert hasattr(agent.config.llm, "generate")

    tool_names = {tool.name for tool in agent.config.tools}
    assert "list" in tool_names
    assert "recall" in tool_names

    # Custom tools
    mock_tool = MagicMock()
    mock_tool.name = "custom_tool"
    agent = Agent(tools=[mock_tool])
    assert len(agent.config.tools) == 1
    assert agent.config.tools[0].name == "custom_tool"


@pytest.mark.asyncio
async def test_execution():
    """Agent executes with proper streaming, context, and error handling."""
    agent = Agent()

    # Successful execution
    with patch("cogency.core.agent.stream") as mock_stream:

        async def mock_events():
            yield {"type": "respond", "content": "Test response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        response = await agent("Hello", user_id="test_user")
        assert response == "Test response"

        mock_stream.assert_called_once()
        call_args = mock_stream.call_args
        config = call_args[0][0]
        user_id = call_args[0][2]
        assert isinstance(config, Config)
        assert user_id == "test_user"

    # Error handling
    with patch("cogency.core.agent.stream") as mock_stream:

        async def mock_failing_events():
            raise RuntimeError("Stream execution failed")
            yield

        mock_stream.return_value = mock_failing_events()

        with pytest.raises(RuntimeError, match="Agent execution failed"):
            await agent("Test query")

    # Empty response handling
    with patch("cogency.core.agent.stream") as mock_stream:

        async def mock_empty_events():
            yield {"type": "think", "content": "Just thinking"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_empty_events()

        with pytest.raises(RuntimeError, match="Agent execution failed"):
            await agent("Test query")
