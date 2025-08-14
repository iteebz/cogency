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
        patch("cogency.reason.reason") as mock_reason,
        patch("cogency.act.act") as mock_act,
        patch("cogency.context.memory.Memory") as mock_memory_class,
        patch("cogency.context.task.start_task") as mock_start_task,
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

        # Mock domain primitives with proper conversation
        from cogency.context.conversation import Conversation
        from cogency.context.execution import Execution
        from cogency.context.session import TaskSession
        from cogency.context.working import WorkingState

        mock_session = TaskSession(query="test query", user_id="test_user")
        mock_conversation = Conversation(
            conversation_id="test-conversation-id", user_id="test_user", messages=[]
        )
        mock_working_state = WorkingState(objective="test query")
        mock_execution = Execution(max_iterations=5)

        mock_start_task.return_value = (
            mock_session,
            mock_conversation,
            mock_working_state,
            mock_execution,
        )

        mock_memory = Mock()
        mock_memory.load = AsyncMock(return_value={})
        mock_memory.remember = AsyncMock()
        mock_memory.update = AsyncMock()
        mock_memory.activate = AsyncMock(return_value="Mock memory context")
        mock_memory_class.return_value = mock_memory

        yield
