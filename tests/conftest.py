"""Test configuration - mock LLM for testing."""
import pytest
from unittest.mock import AsyncMock, patch
from cogency.llm.base import BaseLLM
import tempfile
import shutil
from pathlib import Path


class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def __init__(self, response: str = "Mock response", **kwargs):
        super().__init__(**kwargs)
        self.response = response
    
    async def invoke(self, messages, **kwargs):
        return self.response
    
    async def stream(self, messages, yield_interval: float = 0.0, **kwargs):
        for char in self.response:
            yield char


@pytest.fixture
def mock_llm():
    """Provide mock LLM for tests."""
    return MockLLM()

@pytest.fixture
def mock_llm_response():
    """Fixture to mock GeminiLLM.invoke for integration tests."""
    with patch('cogency.llm.gemini.GeminiLLM.invoke') as mock_invoke:
        yield mock_invoke

@pytest.fixture
def tmp_memory_dir():
    """Provides a temporary directory for memory storage and cleans it up."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
async def fs_memory_instance(tmp_memory_dir):
    """Provides an FSMemory instance and ensures its cleanup."""
    from cogency.memory.backends.filesystem import FilesystemBackend
    memory = FilesystemBackend(memory_dir=tmp_memory_dir)
    yield memory
    await memory._cleanup_tasks()
    memory._executor.shutdown(wait=True)
