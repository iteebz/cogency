#!/usr/bin/env python3
"""Test adaptive routing behavior - fast_react vs deep_react."""

import pytest
from unittest.mock import AsyncMock

from cogency.llm.mock import MockLLM
from cogency.nodes.preprocess import preprocess
from cogency import State
from cogency.context import Context
from cogency.tools.base import BaseTool


class MockSearchTool(BaseTool):
    """Mock search tool for testing."""
    
    def __init__(self):
        super().__init__("search", "Search for information", "🔍")
    
    def schema(self):
        return "search(query: str) -> str"
    
    def examples(self):
        return ["search('weather today')", "search('python tutorials')"]
    
    async def run(self, query: str) -> str:
        return f"Search results for: {query}"


@pytest.mark.asyncio
async def test_routing_fast_react():
    """Test that simple queries get fast_react."""
    llm = MockLLM()
    tools = [MockSearchTool()]
    
    query = "What is the weather today?"
    llm.response = '{"respond_directly": false, "react_mode": "fast", "selected_tools": ["search"], "reasoning": "Simple query"}'
    
    context = Context(query=query)
    from cogency.output import Output
    state = State(query=query, context=context, output=Output())
    
    result = await preprocess(state, llm=llm, tools=tools, memory=None)
    
    assert result.get("next_node") == "reason"

@pytest.mark.asyncio
async def test_routing_deep_react():
    """Test that complex queries get deep_react."""
    llm = MockLLM()
    tools = [MockSearchTool()]
    
    query = "Analyze the economic implications of AI development and compare different regulatory approaches across multiple countries, synthesizing policy recommendations."
    llm.response = '{"respond_directly": false, "react_mode": "deep", "selected_tools": ["search"], "reasoning": "Complex analysis needed"}'
    
    context = Context(query=query)
    from cogency.output import Output
    state = State(query=query, context=context, output=Output())
    
    result = await preprocess(state, llm=llm, tools=tools, memory=None)
    
    assert result.get("next_node") == "reason"

@pytest.mark.asyncio
async def test_routing_direct_response():
    """Test that direct response queries are routed correctly."""
    llm = MockLLM()
    tools = [MockSearchTool()]
    
    query = "Hello, how are you?"
    llm.response = '{"respond_directly": true, "reasoning": "Simple greeting"}'
    
    context = Context(query=query)
    from cogency.output import Output
    state = State(query=query, context=context, output=Output())
    
    result = await preprocess(state, llm=llm, tools=tools, memory=None)
    
    assert result.get("next_node") == "respond"