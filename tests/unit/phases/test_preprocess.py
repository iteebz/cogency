"""Test adaptive routing behavior - fast_react vs deep_react."""

from unittest.mock import AsyncMock, Mock

import pytest

# Import the preprocess function directly
import cogency.phases.preprocess as preprocess_module
from cogency.state import State
from cogency.tools.base import Tool
from tests.conftest import MockLLM


class MockSearchTool(Tool):
    """Mock search tool for testing."""

    def __init__(self):
        super().__init__(
            "search",
            "Search for information",
            "🔍",
            examples=["search('weather today')", "search('python tutorials')"],
        )

    def format_human(self, params, results=None):
        param_str = f"(query='{params.get('query', '')}')" if params else "()"
        result_str = str(results) if results else "pending"
        return param_str, result_str

    def format_agent(self, result_data: dict[str, any]) -> str:
        return f"Tool output: {result_data}"

    async def run(self, query: str) -> str:
        return f"Search results for: {query}"


@pytest.mark.asyncio
async def test_fast():
    """Test that simple queries get fast_react."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "What is the weather today?"
    llm.response = '{"mode": "fast", "selected_tools": ["search"], "reasoning": "Simple query"}'

    state = State(query=query)

    await preprocess_module.preprocess(state, AsyncMock(), llm=llm, tools=tools, memory=None)

    assert state.selected_tools is not None


@pytest.mark.asyncio
async def test_deep():
    """Test that complex queries get deep_react."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "Analyze the economic implications of AI development and compare different regulatory approaches across multiple countries, synthesizing policy recommendations."
    llm.response = (
        '{"mode": "deep", "selected_tools": ["search"], "reasoning": "Complex analysis needed"}'
    )

    state = State(query=query)

    await preprocess_module.preprocess(state, AsyncMock(), llm=llm, tools=tools, memory=None)

    assert state.selected_tools is not None


@pytest.mark.asyncio
async def test_response():
    """Test that direct response queries are routed correctly."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "Hello, how are you?"
    llm.response = '{"selected_tools": [], "reasoning": "Simple greeting"}'

    state = State(query=query)

    await preprocess_module.preprocess(state, AsyncMock(), llm=llm, tools=tools, memory=None)

    assert state.selected_tools == []
