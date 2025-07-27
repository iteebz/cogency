"""Shared test fixtures for cogency unit tests."""

import tempfile
from typing import AsyncIterator

import pytest
from resilient_result import Result

from cogency.context import Context
from cogency.memory.backends.filesystem import FileBackend
from cogency.services.llm.base import BaseLLM
from cogency.state import State
from cogency.tools.base import BaseTool


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
            provider_name="mock",
            api_keys=api_keys,
            enable_cache=enable_cache,
            model=model,
            **kwargs,
        )
        self.response = response
        self.should_fail = should_fail
        self._model = model

    @property
    def default_model(self) -> str:
        """Default model for mock provider."""
        return "mock-model"

    def _get_client(self):
        """Get mock client instance."""
        return self  # Mock client is self

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

    return State(context=context, query="test query")


@pytest.fixture
def tools():
    """Mock tools fixture for testing."""

    class MockTool(BaseTool):
        def __init__(self):
            super().__init__(
                name="mock_tool",
                description="Mock tool for testing",
                emoji="🔧",
                examples=["mock_tool(arg='test')"],
                rules=["Mock tool for testing"],
            )

        async def run(self, **kwargs):
            return Result.ok(f"Mock tool called with {kwargs}")

    return [MockTool()]


@pytest.fixture
def base_agent():
    """Minimal BaseAgent for smoke tests (fixture)."""

    class BaseAgent:
        """Minimal agent for smoke test validation."""

        def __init__(self, llm=None, tools=None, max_iterations=10):
            self.llm = llm
            self.tools = tools or []
            self.max_iterations = max_iterations
            self.messages = []

        async def run(self, prompt: str) -> Result:
            """Run agent with basic tool calling logic."""
            self.messages = [{"role": "user", "content": prompt}]
            for _iteration in range(self.max_iterations):
                llm_result = await self.llm.run(self.messages)
                if not llm_result.success:
                    return Result.fail(f"LLM failed: {llm_result.error}")
                response = llm_result.data
                self.messages.append({"role": "assistant", "content": response})
                if (
                    any(
                        tool_name in response.lower()
                        for tool_name in ["ls", "cat", "ps", "df", "echo"]
                    )
                    and self.tools
                ):
                    command = self._extract_command(response)
                    if command:
                        tool_result = await self.tools[0].call(command)
                        if tool_result.success:
                            self.messages.append(
                                {"role": "user", "content": f"Tool output: {tool_result.data}"}
                            )
                        else:
                            self.messages.append(
                                {
                                    "role": "user",
                                    "content": f"Tool error: {tool_result.error}. Please try a different approach.",
                                }
                            )
                        continue
                return Result.ok(response)
            return Result.fail("Max iterations reached")

        def _extract_command(self, response: str) -> str:
            lines = response.split("\n")
            for line in lines:
                line = line.strip()
                if any(cmd in line for cmd in ["ls", "cat", "ps", "df", "echo"]):
                    return line.split(":")[-1].strip() if ":" in line else line
            return ""

    return BaseAgent


@pytest.fixture
def mock_tool():
    """Mock tool for testing."""

    class MockTool(BaseTool):
        def __init__(self):
            super().__init__(
                name="mock_tool",
                description="Mock tool for testing",
                emoji="🔧",
                examples=["mock_tool(arg='test')"],
                rules=["Mock tool for testing"],
            )

        async def run(self, **kwargs):
            return Result.ok(f"Mock tool called with {kwargs}")

    return MockTool()
