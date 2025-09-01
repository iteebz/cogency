"""Agent tests - Business logic and integration coverage.

FOCUSED TESTING:
1. Agent configuration and defaults
2. Tool integration and filtering
3. Provider selection logic
4. Mode selection behavior
5. Error handling and edge cases
"""

from unittest.mock import MagicMock, patch

import pytest

from cogency import Agent
from cogency.core.config import Config


def test_imports():
    """Agent imports from cogency package."""
    agent = Agent()
    assert agent is not None
    assert callable(agent)
    assert hasattr(agent, "llm")
    assert hasattr(agent, "tools")


def test_config():
    """Agent accepts configuration."""
    agent = Agent(llm="gemini", tools=[], profile=True, sandbox=False)
    assert agent.profile is True
    assert agent.sandbox is False
    assert len(agent.tools) == 0

    # Default tools
    agent_default = Agent()
    assert len(agent_default.tools) > 0


@pytest.mark.asyncio
async def test_call_interface():
    """Agent callable interface works."""
    agent = Agent()

    # Mock the streaming function to avoid complex provider mocking
    with patch("cogency.core.agent.consciousness_stream") as mock_stream:
        # Mock async generator
        async def mock_events():
            yield {"type": "respond", "content": "Test response"}

        mock_stream.side_effect = lambda *args, **kwargs: mock_events()

        # Test basic call pattern
        response = await agent("Hello")
        assert isinstance(response, str)
        assert "Test response" in response

        # Test with user_id
        response = await agent("Hello", user_id="test_user")
        assert isinstance(response, str)


class TestToolsIntegration:
    """Agent tool integration - business logic validation."""

    def test_default_tools_loaded(self):
        """Agent loads default tools correctly."""
        agent = Agent()

        # Should have basic tools by default
        assert len(agent.tools) > 0

        # Tools should be accessible - check actual tool names in list
        tool_names = {tool.name for tool in agent.tools}
        assert "list" in tool_names  # File list tool
        assert "search" in tool_names or "scrape" in tool_names  # Web tools
        assert "recall" in tool_names  # Memory tool


class TestAgentConfiguration:
    """Agent configuration - business logic validation."""

    def test_default_configuration(self):
        """Agent has sane defaults - no configuration needed."""
        agent = Agent()

        # Default LLM should be set
        assert agent.llm is not None
        assert hasattr(agent.llm, "generate")

        # Should have basic tools
        assert len(agent.tools) > 0
        tool_names = {tool.name for tool in agent.tools}
        assert "list" in tool_names
        assert "recall" in tool_names

        # Default behavior flags
        assert agent.profile is True  # Memory enabled by default
        assert agent.sandbox is True  # Safe execution by default
        assert agent.max_iterations > 0

    def test_llm_provider_selection(self):
        """Agent selects LLM providers correctly."""
        # String provider selection
        agent_gemini = Agent(llm="gemini")
        assert hasattr(agent_gemini.llm, "generate")

        agent_openai = Agent(llm="openai")
        assert hasattr(agent_openai.llm, "generate")

        # Should be different instances
        assert type(agent_gemini.llm).__name__ != type(agent_openai.llm).__name__

    def test_tool_filtering(self):
        """Agent filters tools correctly."""
        # Empty tools list
        agent_no_tools = Agent(tools=[])
        assert len(agent_no_tools.tools) == 0

        # Custom tools
        mock_tool = MagicMock()
        mock_tool.name = "custom_tool"

        agent_custom = Agent(tools=[mock_tool])
        assert len(agent_custom.tools) == 1
        assert agent_custom.tools[0].name == "custom_tool"

    def test_behavior_flags(self):
        """Agent behavior flags work correctly."""
        # Profile disabled
        agent_no_profile = Agent(profile=False)
        assert agent_no_profile.profile is False

        # Sandbox disabled
        agent_no_sandbox = Agent(sandbox=False)
        assert agent_no_sandbox.sandbox is False

        # Custom iterations
        agent_custom_iter = Agent(max_iterations=10)
        assert agent_custom_iter.max_iterations == 10


class TestAgentExecution:
    """Agent execution - business logic testing."""

    @pytest.mark.asyncio
    async def test_mode_auto_selection(self):
        """Agent selects execution mode automatically."""
        agent = Agent()

        with patch("cogency.core.agent.consciousness_stream") as mock_stream:
            # Mock successful execution
            async def mock_events():
                yield {"type": "respond", "content": "Auto mode response"}

            mock_stream.side_effect = lambda *args, **kwargs: mock_events()

            response = await agent("Test query")
            assert "Auto mode response" in response

            # Should have called consciousness_stream with config
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            config = call_args[0][0]  # First argument should be config
            assert isinstance(config, Config)
            assert config.mode == "auto"

    @pytest.mark.asyncio
    async def test_user_context_handling(self):
        """Agent handles user context correctly."""
        agent = Agent()

        with patch("cogency.core.agent.consciousness_stream") as mock_stream:

            async def mock_events():
                yield {"type": "respond", "content": "User context response"}

            mock_stream.side_effect = lambda *args, **kwargs: mock_events()

            # Test with user_id
            response = await agent("Query", user_id="test_user")
            assert isinstance(response, str)

            # Should pass user_id to consciousness_stream
            call_args = mock_stream.call_args
            user_id = call_args[0][2]  # Third argument should be user_id
            assert user_id == "test_user"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Agent handles execution errors gracefully."""
        agent = Agent()

        with patch("cogency.core.agent.consciousness_stream") as mock_stream:
            # Mock stream that raises exception
            async def mock_failing_events():
                raise RuntimeError("Stream execution failed")
                yield  # Unreachable but makes it an async generator

            mock_stream.return_value = mock_failing_events()

            # Should propagate the error with "Execution failed:" prefix
            with pytest.raises(RuntimeError, match="Execution failed:"):
                await agent("Test query")

    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        """Agent handles empty responses correctly."""
        agent = Agent()

        with patch("cogency.core.agent.consciousness_stream") as mock_stream:
            # Mock stream with no respond events
            async def mock_empty_events():
                yield {"type": "think", "content": "Just thinking"}
                # No respond event

            mock_stream.side_effect = lambda *args, **kwargs: mock_empty_events()

            response = await agent("Test query")
            # Should get default message when no respond events
            assert response == "Execution completed"
