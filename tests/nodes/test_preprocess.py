#!/usr/bin/env python3
"""Test adaptive routing behavior - fast_react vs deep_react."""

import pytest

from cogency import State
from cogency.context import Context
from cogency.services.llm.mock import MockLLM
from cogency.nodes.preprocess import preprocess
from cogency.tools.base import BaseTool


class MockSearchTool(BaseTool):
    """Mock search tool for testing."""

    def __init__(self):
        super().__init__(
            "search",
            "Search for information",
            "🔍",
            schema="search(query: str) -> str",
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
async def test_routing_fast_react():
    """Test that simple queries get fast_react."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "What is the weather today?"
    llm.response = (
        '{"react_mode": "fast", "selected_tools": ["search"], "reasoning": "Simple query"}'
    )

    context = Context(query=query)
    from cogency.output import Output

    state = State(query=query, context=context, output=Output())

    await preprocess(state, llm=llm, tools=tools, memory=None)

    assert state.get("respond_directly") is False


@pytest.mark.asyncio
async def test_routing_deep_react():
    """Test that complex queries get deep_react."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "Analyze the economic implications of AI development and compare different regulatory approaches across multiple countries, synthesizing policy recommendations."
    llm.response = '{"react_mode": "deep", "selected_tools": ["search"], "reasoning": "Complex analysis needed"}'

    context = Context(query=query)
    from cogency.output import Output

    state = State(query=query, context=context, output=Output())

    await preprocess(state, llm=llm, tools=tools, memory=None)

    assert state.get("respond_directly") is False


@pytest.mark.asyncio
async def test_routing_direct_response():
    """Test that direct response queries are routed correctly."""
    llm = MockLLM()
    tools = [MockSearchTool()]

    query = "Hello, how are you?"
    llm.response = '{"selected_tools": [], "reasoning": "Simple greeting"}'

    context = Context(query=query)
    from cogency.output import Output

    state = State(query=query, context=context, output=Output())

    await preprocess(state, llm=llm, tools=tools, memory=None)

    assert state.get("respond_directly") is True
