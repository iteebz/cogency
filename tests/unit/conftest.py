import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from cogency.llm.mock import MockLLM
from cogency.memory.filesystem import FSMemory
from cogency.tools.base import BaseTool
from cogency.tools.registry import ToolRegistry
from cogency.tools.recall import RecallTool

@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    return MockLLM(response="Mock LLM response")

@pytest.fixture
def mock_tool():
    """Mock tool for testing."""
    tool = MagicMock(spec=BaseTool)
    tool.name = "mock_tool"
    tool.description = "A mock tool"
    tool.parameters = {}
    tool.run = AsyncMock(return_value="Mock tool output")
    return tool

@pytest.fixture
def fs_memory_fixture(tmp_path):
    """Fixture for FSMemory instance with a temporary directory."""
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir()
    return FSMemory(memory_dir=str(memory_dir))

@pytest.fixture(autouse=True)
def setup_tool_registry():
    """Ensure ToolRegistry is populated for tests."""
    # Clear existing tools to prevent interference between tests
    ToolRegistry.clear()
    # Register memory tool classes explicitly for testing auto-discovery
    ToolRegistry.register(RecallTool)
    yield
    # Clean up after tests
    ToolRegistry.clear()