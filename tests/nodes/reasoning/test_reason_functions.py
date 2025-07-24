"""Tests for reason node utility functions."""

from unittest.mock import Mock

import pytest

from cogency.nodes.reason import format_actions
from cogency.tools.base import BaseTool
from cogency.utils.results import ExecutionResult


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, name: str):
        super().__init__(name=name, description="test tool", emoji="🔧", schema="test")

    async def run(self, **kwargs):
        return {"test": "result"}

    def format_human(self, params, results=None):
        """Format for human display."""
        return "test", "result"

    def format_agent(self, result_data):
        """Format results for agent history."""
        if not result_data:
            return "No results"
        query = result_data.get("query", "unknown")
        results = result_data.get("results", [])
        return f"'{query}' → Found {len(results)} results"


class TestFormatAgentResults:
    """Test format_agent_results function."""

    def test_format_agent_results_success(self):
        """Test successful result extraction with real execution structure."""
        # Create mock tools
        search_tool = MockTool("search")
        selected_tools = [search_tool]

        # Create tool calls (as they come from reason node)
        tool_calls = [{"name": "search", "args": {"query": "test query", "max_results": 3}}]

        # Create execution results (as they come from act node)
        execution_results = ExecutionResult.ok(
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
        result = format_agent_results(execution_results, tool_calls, selected_tools)

        # Should call format_agent on the search tool with the result data
        assert result == "'test query' → Found 2 results"

    def test_format_agent_results_multiple_tools(self):
        """Test with multiple tools executed."""
        # Create mock tools
        search_tool = MockTool("search")
        scrape_tool = MockTool("scrape")
        scrape_tool.format_agent = lambda data: f"Scraped: {data.get('title', 'untitled')}"

        selected_tools = [search_tool, scrape_tool]

        tool_calls = [
            {"name": "search", "args": {"query": "test"}},
            {"name": "scrape", "args": {"url": "http://example.com"}},
        ]

        execution_results = ExecutionResult.ok(
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

        result = format_agent_results(execution_results, tool_calls, selected_tools)

        # Should join results from both tools
        assert result == "'test' → Found 1 results | Scraped: Test Page"

    def test_format_agent_results_no_execution_results(self):
        """Test with no execution results."""
        result = format_agent_results(None, [], [])
        assert result == ""

        # Test with execution results but no data
        empty_results = ExecutionResult.ok(None)
        result = format_agent_results(empty_results, [], [])
        assert result == ""

    def test_format_agent_results_malformed_data(self):
        """Test with malformed execution results."""
        # Missing 'results' key
        bad_results = ExecutionResult.ok({"summary": "test"})
        result = format_agent_results(bad_results, [], [])
        assert result == ""

        # Wrong data type
        bad_results = ExecutionResult.ok("not a dict")
        result = format_agent_results(bad_results, [], [])
        assert result == ""

    def test_format_agent_results_tool_not_found(self):
        """Test when tool is not found in selected_tools."""
        tool_calls = [{"name": "unknown_tool", "args": {}}]
        execution_results = ExecutionResult.ok(
            {"results": [{"tool_name": "unknown_tool", "result": {"test": "data"}}]}
        )

        result = format_agent_results(execution_results, tool_calls, [])
        assert result == ""  # No matching tool found

    def test_format_agent_results_empty_result_data(self):
        """Test when tool result data is empty."""
        search_tool = MockTool("search")
        tool_calls = [{"name": "search", "args": {}}]
        execution_results = ExecutionResult.ok(
            {"results": [{"tool_name": "search", "result": {}}]}  # Empty result
        )

        result = format_agent_results(execution_results, tool_calls, [search_tool])
        assert result == "No results"  # format_agent handles empty data
