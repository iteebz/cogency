"""Shared test fixtures and utilities for Cogency test suite."""
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from cogency.context import Context
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.llm.mock import MockLLM
from cogency.tools.calculator import CalculatorTool
from cogency.tools.weather import WeatherTool
from cogency.types import AgentState


@pytest.fixture
def temp_memory_dir():
    """Temporary directory for memory backend testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def memory_backend(temp_memory_dir):
    """Filesystem memory backend for testing."""
    return FilesystemBackend(memory_dir=temp_memory_dir)


@pytest.fixture
def mock_llm():
    """Mock LLM for deterministic testing."""
    return MockLLM()


@pytest.fixture
def context():
    """Basic agent context for testing."""
    return Context(
        current_input="test query",
        messages=[],
        user_id="test_user"
    )


@pytest.fixture
def agent_state(context):
    """Basic agent state for workflow testing."""
    return AgentState(
        context=context,
        trace=None,
        query="test query",
        last_node_output=None
    )


@pytest.fixture
def tools():
    """Standard tool set for testing."""
    return [
        CalculatorTool(),
        WeatherTool()
    ]


@pytest.fixture
def sample_memory_content():
    """Sample content for memory testing."""
    return [
        {"content": "I have ADHD and work as a software engineer", "tags": ["personal", "work"]},
        {"content": "I prefer quiet environments for coding", "tags": ["preferences"]},
        {"content": "I live in San Francisco", "tags": ["personal", "location"]},
        {"content": "Python is my favorite programming language", "tags": ["preferences", "tech"]}
    ]


class TestHelpers:
    """Utility methods for testing."""
    
    @staticmethod
    def assert_valid_tool_call(tool_call: Dict[str, Any]):
        """Assert tool call has required structure."""
        assert "name" in tool_call
        assert "args" in tool_call
        assert isinstance(tool_call["args"], dict)
    
    @staticmethod
    def assert_memory_artifact_valid(artifact):
        """Assert memory artifact has required fields."""
        assert artifact.id is not None
        assert artifact.content
        assert artifact.created_at is not None
        assert isinstance(artifact.tags, list)
        assert isinstance(artifact.metadata, dict)
    
    @staticmethod
    def assert_no_errors_in_result(result: Dict[str, Any]):
        """Assert result doesn't contain error fields."""
        assert "error" not in result, f"Unexpected error: {result.get('error')}"


@pytest.fixture
def helpers():
    """Test helper methods."""
    return TestHelpers


# Code quality fixtures for anti-pattern detection
@pytest.fixture
def source_files():
    """All Python source files for quality checks."""
    src_dir = Path(__file__).parent.parent / "src" / "cogency"
    return list(src_dir.rglob("*.py"))