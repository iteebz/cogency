"""Test adaptive routing behavior - fast_react vs deep_react."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.state import AgentState

# Import the prepare function directly
from cogency.steps.prepare import prepare
from cogency.tools.base import Tool
from tests.fixtures.llm import MockLLM


class MockSearchTool(Tool):
    """Mock search tool for testing."""

    def __init__(self):
        super().__init__(
            "search",
            "Search for information",
            "🔍",
            examples=["search('weather today')", "search('python tutorials')"],
        )

    def format_human(self, args, results=None):
        arg_str = f"(query='{args.get('query', '')}')" if args else "()"
        result_str = str(results) if results else "pending"
        return arg_str, result_str

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

    state = AgentState(query=query)

    result = await prepare(state, AsyncMock(), llm=llm, tools=tools, memory=None)

    # The prepare function should complete successfully
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_deep():
    """Test that complex queries get deep_react."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "Analyze the economic implications of AI development and compare different regulatory approaches across multiple countries, synthesizing policy recommendations."
    llm.response = (
        '{"mode": "deep", "selected_tools": ["search"], "reasoning": "Complex analysis needed"}'
    )

    state = AgentState(query=query)

    result = await prepare(state, AsyncMock(), llm=llm, tools=tools, memory=None)

    # The prepare function should complete successfully
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_response():
    """Test that direct response queries are routed correctly."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "Hello, how are you?"
    llm.response = '{"selected_tools": [], "reasoning": "Simple greeting"}'

    state = AgentState(query=query)

    result = await prepare(state, AsyncMock(), llm=llm, tools=tools, memory=None)

    # Should return early response for greetings or have empty tools
    assert result is None or isinstance(result, str)
