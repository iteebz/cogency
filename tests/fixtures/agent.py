"""Agent fixtures."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.agent import Agent
from tests.fixtures.provider import MockLLM


@pytest.fixture
def agent():
    """Basic agent with fast mocks."""
    agent = Agent("test-agent")
    agent.llm = MockLLM(response='{"reasoning": "test", "response": "Fast mock response"}')
    return agent


@pytest.fixture
def agent_with_memory():
    """Agent with mocked memory system."""
    mock_memory = Mock()
    mock_memory.load = AsyncMock()
    mock_memory.remember = AsyncMock()
    mock_memory.update = AsyncMock()

    return Agent("test-agent", memory=mock_memory)


@pytest.fixture
def agent_with_tools():
    """Agent with Files and Shell tools."""
    from cogency.tools import Files, Shell

    return Agent("test-agent", tools=[Files(), Shell()])


@pytest.fixture
def agent_full():
    """Full-featured agent for integration tests."""
    from cogency.tools import Files, Shell

    return Agent("test-full", tools=[Files(), Shell()], memory=True)


@pytest.fixture(autouse=True)
def mock_agent_execution(request):
    """Auto-mock slow agent execution for fast tests."""
    # Skip mocking for integration tests
    if hasattr(request, "node") and any(
        mark.name == "integration" for mark in request.node.iter_markers()
    ):
        yield  # No mocking for integration tests
        return

    with (
        patch("cogency.agents.reason") as mock_reason,
        patch("cogency.agents.act") as mock_act,
        patch("cogency.memory.Memory") as mock_memory_class,
        patch("cogency.state.State.start_task") as mock_start_task,
    ):
        from resilient_result import Result

        # Fast mock responses
        mock_reason.return_value = Result.ok(
            {
                "reasoning": "Mock reasoning",
                "response": "Mock response from fast mocked agent",
                "actions": [],
            }
        )

        mock_act.return_value = Result.ok(
            {
                "results": [],
                "errors": [],
                "summary": "Mock tool execution",
                "total_executed": 0,
                "successful_count": 0,
                "failed_count": 0,
            }
        )

        # Mock state with proper conversation
        mock_state = Mock()
        mock_state.context = lambda: "Mock context"
        mock_conversation = Mock()
        mock_conversation.conversation_id = "test-conversation-id"
        mock_state.conversation = mock_conversation
        mock_start_task.return_value = mock_state

        mock_memory = Mock()
        mock_memory.load = AsyncMock(return_value={})
        mock_memory.remember = AsyncMock()
        mock_memory.update = AsyncMock()
        mock_memory.activate = AsyncMock(return_value="Mock memory context")
        mock_memory_class.return_value = mock_memory

        yield
