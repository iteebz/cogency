"""Shared test fixtures for cogency unit tests."""

import tempfile
from typing import AsyncIterator

import pytest

from cogency.context import Context
from cogency.services.llm.base import BaseLLM
from cogency.services.memory.filesystem import FileBackend
from cogency.state import State
from cogency.utils.results import ToolResult


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(
        self,
        response: str = "Mock response",
        should_fail: bool = False,
        api_keys: str = "mock_key",
        enable_cache: bool = False,
        model: str = "mock-model",
        **kwargs,
    ):
        super().__init__(
            provider_name="mock", api_keys=api_keys, enable_cache=enable_cache, **kwargs
        )
        self.response = response
        self.should_fail = should_fail
        self.model = model

    async def _run_impl(self, messages, **kwargs) -> str:
        if self.should_fail:
            raise Exception("Mock LLM failure")
        return self.response

    async def stream(self, messages, **kwargs) -> AsyncIterator[str]:
        for char in self.response:
            yield char


def create_mock_llm(response: str, **kwargs):
    """Create a mock LLM with specified response."""
    return MockLLM(response=response, **kwargs)


@pytest.fixture
def temp_dir():
    """Temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def memory_service(temp_dir):
    """Filesystem memory backend."""
    return FileBackend(memory_dir=temp_dir)


@pytest.fixture
def mock_llm():
    """Mock LLM instance."""
    return MockLLM()


@pytest.fixture
def context():
    """Basic context."""
    return Context(query="test query", messages=[], user_id="test_user")


@pytest.fixture
def agent_state(context):
    """Basic agent state."""
    from cogency.output import Output

    return State(context=context, query="test query", output=Output())


@pytest.fixture
def tools():
    """Mock tools fixture for testing."""

    class MockTool:
        name = "mock_tool"

        def __init__(self):
            pass

        async def run(self, **kwargs):
            return ToolResult(f"Mock tool called with {kwargs}")

    return [MockTool()]


@pytest.fixture
def mock_tool():
    """Mock tool for testing."""

    class MockTool:
        name = "mock_tool"

        def __init__(self):
            pass

        async def run(self, **kwargs):
            return ToolResult(f"Mock tool called with {kwargs}")

    return MockTool()
