"""Canonical test fixtures - zero ceremony testing."""

from unittest.mock import patch

import pytest

from cogency.state import State
from tests.fixtures.agent import *  # noqa: F403, F401

# Import all fixtures from decomposed modules
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
        patch("cogency.utils.credentials.Credentials.detect", return_value=None),
        patch("cogency.providers.detection._detect_llm_provider", return_value=mock_llm),
        patch("cogency.providers.detection._detect_embed_provider", return_value=mock_embed),
    ):
        yield {"llm": mock_llm, "embed": mock_embed}


@pytest.fixture
def agent_state():
    """Basic agent state."""
    return State(query="test query")


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
