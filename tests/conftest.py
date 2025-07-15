"""Test configuration - mock LLM for testing."""
import pytest
from unittest.mock import AsyncMock
from cogency.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def __init__(self, response: str = "Mock response"):
        self.response = response
    
    async def invoke(self, messages, **kwargs):
        return self.response
    
    async def stream(self, messages, **kwargs):
        for char in self.response:
            yield char


@pytest.fixture
def mock_llm():
    """Provide mock LLM for tests."""
    return MockLLM()