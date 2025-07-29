"""Tests for enhanced reasoning node integration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.phases.reason import format_actions, reason
from cogency.state import State
from cogency.tools.base import Tool
from tests.conftest import MockLLM


class MockToolCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


def mock_llm():
    llm = AsyncMock()
    llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "test reasoning", "strategy": "test_strategy"}')
    )
    return llm


def mock_tools():
    tool = Mock()
    tool.name = "test_tool"
    tool.schema = "test schema"
    tool.examples = []
    tool.rules = []
    return [tool]


def basic_state():
    return State(query="test query")


@pytest.mark.asyncio
async def test_init():
    state = basic_state()
    await reason(state, notify=Mock(), llm=mock_llm(), tools=mock_tools())

    assert isinstance(state, State)
    assert hasattr(state, "objective")
    assert hasattr(state, "understanding")
    assert hasattr(state, "approach")
    assert hasattr(state, "discoveries")
    assert isinstance(state.actions, list)
    assert hasattr(state, "attempts")


@pytest.mark.asyncio
async def test_tracking():
    state = basic_state()
    state.iteration = 2

    await reason(state, notify=Mock(), llm=mock_llm(), tools=mock_tools())

    assert isinstance(state, State)
    assert state.iteration == 3


@pytest.mark.asyncio
async def test_depth():
    state = basic_state()
    state.iteration = 5
    state.depth = 5

    await reason(state, notify=Mock(), llm=mock_llm(), tools=mock_tools())

    assert isinstance(state, State)
    assert state.stop_reason == "depth_reached"


@pytest.mark.asyncio
async def test_error():
    state = basic_state()
    llm = mock_llm()
    llm.run.side_effect = Exception("LLM error")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(Exception, match="LLM error"):
            await reason(state, notify=Mock(), llm=llm, tools=mock_tools())


class MockTool(Tool):
    def __init__(self, name: str):
        super().__init__(name=name, description="test tool", emoji="🔧")

    async def run(self, **kwargs):
        return {"test": "result"}

    def format_human(self, params, results=None):
        return "test", "result"

    def format_agent(self, result_data):
        if not result_data:
            return "No results"
        query = result_data.get("query", "unknown")
        results = result_data.get("results", [])
        return f"'{query}' → Found {len(results)} results"


def test_format_success():
    # Create mock tools
    search_tool = MockTool("search")
    selected_tools = [search_tool]

    # Create tool calls (as they come from reason node)
    tool_calls = [{"name": "search", "args": {"query": "test query", "max_results": 3}}]

    # Create execution results (as they come from act node)
    execution_results = Result.ok(
        {
            "results": [
                {
                    "tool_name": "search",
                    "args": {"query": "test query", "max_results": 3},
                    "result": {
                        "query": "test query",
                        "results": [
                            {"title": "Result 1", "url": "http://example1.com"},
                            {"title": "Result 2", "url": "http://example2.com"},
                        ],
                        "total_found": 2,
                    },
                }
            ],
            "errors": [],
            "summary": "1 tool executed successfully",
        }
    )

    # Test extraction
    result = format_actions(execution_results, tool_calls, selected_tools)

    # Should call format_agent on the search tool with the result data
    assert result == "'test query' → Found 2 results"


def test_format_multi():
    # Create mock tools
    search_tool = MockTool("search")
    scrape_tool = MockTool("scrape")
    scrape_tool.format_agent = lambda data: f"Scraped: {data.get('title', 'untitled')}"

    selected_tools = [search_tool, scrape_tool]

    tool_calls = [
        {"name": "search", "args": {"query": "test"}},
        {"name": "scrape", "args": {"url": "http://example.com"}},
    ]

    execution_results = Result.ok(
        {
            "results": [
                {
                    "tool_name": "search",
                    "args": {"query": "test"},
                    "result": {"query": "test", "results": [{"title": "Test"}]},
                },
                {
                    "tool_name": "scrape",
                    "args": {"url": "http://example.com"},
                    "result": {"title": "Test Page", "content": "Some content"},
                },
            ]
        }
    )

    result = format_actions(execution_results, tool_calls, selected_tools)

    # Should join results from both tools
    assert result == "'test' → Found 1 results | Scraped: Test Page"


def test_format_no_results():
    result = format_actions(None, [], [])
    assert result == ""

    # Test with execution results but no data
    empty_results = Result.ok(None)
    result = format_actions(empty_results, [], [])
    assert result == ""


def test_format_malformed():
    # Missing 'results' key
    bad_results = Result.ok({"summary": "test"})
    result = format_actions(bad_results, [], [])
    assert result == ""

    # Wrong data type
    bad_results = Result.ok("not a dict")
    result = format_actions(bad_results, [], [])
    assert result == ""


def test_format_tool_missing():
    tool_calls = [{"name": "unknown_tool", "args": {}}]
    execution_results = Result.ok(
        {"results": [{"tool_name": "unknown_tool", "result": {"test": "data"}}]}
    )

    result = format_actions(execution_results, tool_calls, [])
    assert result == ""  # No matching tool found


def test_format_empty_data():
    search_tool = MockTool("search")
    tool_calls = [{"name": "search", "args": {}}]
    execution_results = Result.ok(
        {"results": [{"tool_name": "search", "result": {}}]}  # Empty result
    )

    result = format_actions(execution_results, tool_calls, [search_tool])
    assert result == "No results"  # format_agent handles empty data
