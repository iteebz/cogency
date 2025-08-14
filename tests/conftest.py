"""Canonical test fixtures - zero ceremony testing."""

from unittest.mock import patch

import pytest

# Import all fixtures from decomposed modules
from tests.fixtures.agent import *  # noqa: F403, F401
from tests.fixtures.integration import *  # noqa: F403, F401
from tests.fixtures.provider import MockEmbed, MockLLM
from tests.fixtures.storage import *  # noqa: F403, F401
from tests.fixtures.tools import *  # noqa: F403, F401
from tests.fixtures.workspace import *  # noqa: F403, F401


@pytest.fixture
def mock_llm():
    """Fast mock LLM provider."""
    return MockLLM()


@pytest.fixture
def mock_embed():
    """Fast mock embedding provider."""
    return MockEmbed()


@pytest.fixture(autouse=True)
def fast_providers(mock_llm, mock_embed):
    """Canonical fast provider setup - zero ceremony testing."""
    with (
        patch("cogency.providers.utils.credentials.Credentials.detect", return_value=None),
        patch("cogency.providers.utils.detection._detect_llm_provider", return_value=mock_llm),
        patch("cogency.providers.utils.detection._detect_embed_provider", return_value=mock_embed),
    ):
        yield {"llm": mock_llm, "embed": mock_embed}


@pytest.fixture
async def domain_primitives():
    """Domain-centric test data - replaces State container."""
    from cogency.context.task import start_task

    session, conversation, working_state, execution = await start_task(
        query="test query", user_id="test_user", conversation_id=None, max_iterations=5
    )

    return {
        "session": session,
        "conversation": conversation,
        "working_state": working_state,
        "execution": execution,
    }


@pytest.fixture
def mock_domain_primitives():
    """Fast mock domain primitives for unit tests."""
    from cogency.context.conversation import Conversation
    from cogency.context.execution import Execution
    from cogency.context.session import TaskSession
    from cogency.context.working import WorkingState

    # Create real objects with mock data
    session = TaskSession(query="test query", user_id="test_user")
    conversation = Conversation(user_id="test_user", messages=[])
    working_state = WorkingState(objective="test query")
    execution = Execution(max_iterations=5)

    return {
        "session": session,
        "conversation": conversation,
        "working_state": working_state,
        "execution": execution,
    }


@pytest.fixture
def mock_responses():
    """LLM response fixtures."""
    return {
        "simple": "This is a simple response.",
        "tool_usage": "I'll use a tool to help with that.",
        "error": "I encountered an error while processing.",
    }


@pytest.fixture
def mock_search_engine():
    """Mock search engine for testing Search tool."""
    from unittest.mock import patch

    with patch("cogency.tools.search.DDGS") as mock_ddgs:
        with patch("asyncio.sleep") as mock_sleep:
            yield mock_ddgs, mock_sleep
