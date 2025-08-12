"""Canonical test fixtures - DRY principle via conftest.py."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.agent import Agent
from cogency.state import State

# Import all fixtures from decomposed modules
from tests.fixtures.provider import MockProvider
from tests.fixtures.tools import MockTool


@pytest.fixture
def temp_dir():
    """Temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def agent():
    """Basic agent instance."""
    return Agent("test-agent")


@pytest.fixture
def agent_with_memory():
    """Agent with memory system."""
    # Mock Memory to avoid real persistence during tests
    mock_memory = Mock()
    mock_memory.load = AsyncMock()
    mock_memory.remember = AsyncMock()
    mock_memory.update = AsyncMock()

    return Agent("test-agent", memory=mock_memory)


@pytest.fixture
def agent_with_tools():
    """Agent with Files and Shell tools."""
    return Agent("test-agent", tools=["files", "shell"])


@pytest.fixture
def mock_responses():
    """LLM response fixtures."""
    return {
        "simple": "This is a simple response.",
        "tool_usage": "I'll use a tool to help with that.",
        "error": "I encountered an error while processing.",
    }


@pytest.fixture
def temp_workspace():
    """Isolated test environment with workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_dir = Path(tmpdir) / "workspace"
        workspace_dir.mkdir()

        # Create test files
        (workspace_dir / "test.txt").write_text("Test content")
        (workspace_dir / "data.json").write_text('{"test": true}')

        yield workspace_dir


@pytest.fixture
def agent_state():
    """Basic agent state."""
    return State(query="test query")


@pytest.fixture
def temp_docs_dir():
    """Temporary directory with test documents for retrieval testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir()

        # Create test documents
        (docs_dir / "readme.md").write_text(
            "# Project Documentation\nThis is a test project with authentication features."
        )
        (docs_dir / "auth.md").write_text(
            "# Authentication\nUsers can login with username and password. JWT tokens are used for sessions."
        )
        (docs_dir / "api.md").write_text(
            "# API Reference\nThe API supports rate limiting at 1000 requests per hour."
        )

        yield docs_dir


@pytest.fixture
def mock_llm_error():
    """Mock LLM that raises errors for testing."""
    provider = Mock()
    provider.generate = AsyncMock(side_effect=Exception("API Error"))
    return provider


@pytest.fixture
def mock_embedder():
    """Mock embedding provider for testing."""
    embedder = Mock()
    embedder.embed = AsyncMock()
    return embedder


@pytest.fixture
def mock_provider():
    """Mock provider for testing."""
    return MockProvider()


@pytest.fixture
def mock_tools():
    """Mock tools list for testing."""
    return [MockTool()]


# Integration test fixtures
@pytest.fixture
def agent_basic():
    """Basic agent for integration tests."""
    return Agent("test-basic")


@pytest.fixture
def agent_full():
    """Full-featured agent for integration tests."""
    return Agent("test-full", tools=["files", "shell"], memory=True)


@pytest.fixture
def workspace():
    """Workspace fixture (alias for temp_workspace)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_dir = Path(tmpdir) / "workspace"
        workspace_dir.mkdir()

        # Create test files
        (workspace_dir / "test.txt").write_text("Test content")
        (workspace_dir / "data.json").write_text('{"test": true}')

        yield workspace_dir


@pytest.fixture
def event_monitor():
    """Mock event monitor for integration tests."""
    monitor = Mock()
    monitor.capture_events = Mock(return_value=[])
    monitor.assert_event_types = Mock()
    monitor.assert_event_count = Mock()
    return monitor


@pytest.fixture
def clean_env():
    """Clean environment for testing."""
    return {"clean": True}


@pytest.fixture
def mock_reasoning():
    """Mock reasoning system for agent tests."""
    with patch("cogency.agents.reason") as mock:
        mock.return_value = {"response": "Test response", "actions": []}
        yield mock


@pytest.fixture
def mock_security():
    """Mock security validation for agent tests."""
    with patch("cogency.security.validation.validate_query") as mock:
        mock.return_value = None  # No security violations
        yield mock


@pytest.fixture
def mock_state_creation():
    """Mock state creation for agent tests."""
    with patch("cogency.state.State.start_task") as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture
def mock_action_execution():
    """Mock action execution for agent tests."""
    with patch("cogency.agents.act") as mock:
        mock.return_value = {"success": True}
        yield mock


@pytest.fixture
def mock_search_engine():
    """Mock DuckDuckGo search engine for search tool tests."""
    with patch("cogency.tools.search.DDGS") as mock_ddgs:
        with patch("asyncio.sleep") as mock_sleep:
            yield mock_ddgs, mock_sleep


@pytest.fixture
def memory_session():
    """Mock memory session for integration tests."""
    session = Mock()
    # Create agent with memory enabled
    session.create_agent = Mock(return_value=Agent("test-memory", memory=True))
    session.verify_memory_persistence = Mock()
    return session


@pytest.fixture
def performance_baseline():
    """Mock performance baseline for integration tests."""
    baseline = Mock()

    # Make measure_async return the actual result of the function call
    async def mock_measure_async(name, func, *args, **kwargs):
        return await func(*args, **kwargs)

    baseline.measure_async = AsyncMock(side_effect=mock_measure_async)
    baseline.assert_performance = Mock()
    return baseline


@pytest.fixture
def tool_chain():
    """Mock tool chain validator for integration tests."""
    chain = Mock()
    chain.verify_chain = Mock()
    return chain


@pytest.fixture
async def temp_db():
    """Temporary database for state storage integration tests."""
    from cogency.storage.sqlite import SQLite

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = SQLite(str(db_path))

        # Initialize database
        await storage.init()

        yield storage

        # Cleanup
        await storage.close()
