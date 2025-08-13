"""Tool execution and error handling tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.agent import Agent
from cogency.resilience import resilience, smart_handler


def test_configuration(agent_with_tools):
    """Test agent with tools configuration."""
    # Agent should have Files and Shell tool instances
    assert len(agent_with_tools.tools) == 2
    assert any(tool.__class__.__name__ == "Files" for tool in agent_with_tools.tools)
    assert any(tool.__class__.__name__ == "Shell" for tool in agent_with_tools.tools)


@pytest.mark.asyncio
async def test_execution(agent_with_tools):
    """Test tool execution in agent workflow."""
    # Mock the actual execution path
    with patch("cogency.agents.act", new_callable=AsyncMock) as mock_act:
        with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
            with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
                mock_task = Mock()
                mock_task.conversation.conversation_id = "test_conversation_id"
                mock_state.return_value = mock_task
                mock_reason.return_value = Result.ok({"actions": [{"tool": "files", "args": {}}]})
                mock_act.return_value = "Tool executed successfully"

                response, conversation_id = await agent_with_tools.run(
                    "List files in current directory"
                )
                # Response comes from the reasoning loop, not directly from tools
                assert isinstance(response, str)
                assert isinstance(conversation_id, str)


def test_smart_error_handler():
    """Test smart error classification."""
    # Code bugs should stop retry
    assert smart_handler(TypeError("Invalid type")) is False
    assert smart_handler(AttributeError("Missing attr")) is False
    assert smart_handler(KeyError("Missing key")) is False
    assert smart_handler(ImportError("Missing module")) is False
    assert smart_handler(SyntaxError("Invalid syntax")) is False

    # Network/API errors should retry
    assert smart_handler(Exception("API timeout")) is None
    assert smart_handler(ConnectionError("Network issue")) is None


@pytest.mark.asyncio
async def test_resilience_decorator():
    """Test resilience decorator with smart handler."""

    @resilience
    async def failing_function():
        raise TypeError("This is a code bug")

    # Resilience decorator returns a Result type, not raises
    result = await failing_function()
    assert result.failure
    assert "This is a code bug" in str(result.error)


@pytest.mark.asyncio
async def test_error_recovery(agent_with_tools):
    """Test agent recovery from tool errors."""
    # Mock a tool that fails initially then succeeds
    with patch("cogency.agents.act", new_callable=AsyncMock) as mock_act:
        with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
            with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
                mock_task = Mock()
                mock_task.conversation.conversation_id = "test_conversation_id"
                mock_state.return_value = mock_task
                mock_act.side_effect = [Exception("Tool failed"), "Tool succeeded"]
                mock_reason.return_value = Result.ok({"actions": [{"tool": "files", "args": {}}]})

                # Agent should handle tool errors gracefully
                response, conversation_id = await agent_with_tools.run("Use tool that might fail")
                assert isinstance(response, str)
                assert isinstance(conversation_id, str)


def test_validation():
    """Test tool validation during agent setup."""
    # Empty tools should work
    agent = Agent("test", tools=[])
    assert agent.tools == []

    # String tool names should now raise error (API change)
    with pytest.raises(ValueError, match="Invalid tool type.*Use Tool.*instances"):
        Agent("test", tools=["files"])


@pytest.mark.asyncio
async def test_multiple_execution(agent_with_tools):
    """Test execution with multiple tools."""
    # Test that agent can handle multiple tools
    assert len(agent_with_tools.tools) == 2  # Files and Shell tools

    with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
        with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
            mock_task = Mock()
            mock_task.conversation.conversation_id = "test_conversation_id"
            mock_state.return_value = mock_task
            mock_reason.return_value = Result.ok({"response": "Used multiple tools"})

            response, conversation_id = await agent_with_tools.run(
                "List files and check system info"
            )
            assert response == "Used multiple tools"
            assert isinstance(conversation_id, str)


def test_registry_access(agent_with_tools):
    """Test tool registry functionality."""
    # Agent should have tools attribute
    assert hasattr(agent_with_tools, "tools")

    # Tools should be Files and Shell instances
    assert len(agent_with_tools.tools) == 2


@pytest.mark.asyncio
async def test_isolation(workspace):
    """Test tool execution in isolated workspace."""
    agent = Agent("test", tools=[])

    # Mock file operations to test isolation
    with patch("cogency.agents.act", new_callable=AsyncMock) as mock_act:
        with patch("cogency.agents.reason", new_callable=AsyncMock) as mock_reason:
            with patch("cogency.state.State.start_task", new_callable=AsyncMock) as mock_state:
                mock_task = Mock()
                mock_task.conversation.conversation_id = "test_conversation_id"
                mock_state.return_value = mock_task
                mock_act.return_value = f"Files listed in {workspace}"
                mock_reason.return_value = Result.ok({"actions": [{"tool": "files", "args": {}}]})

                response, conversation_id = await agent.run("List workspace files")
                assert isinstance(response, str)
                assert isinstance(conversation_id, str)


def test_error_types_classification():
    """Test classification of different error types."""
    # Test with basic error types that definitely work
    assert smart_handler(TypeError("Type error")) is False
    assert smart_handler(AttributeError("Attribute error")) is False

    # Runtime errors that should retry
    assert smart_handler(RuntimeError("Temporary failure")) is None
    assert smart_handler(ValueError("API returned invalid value")) is None
