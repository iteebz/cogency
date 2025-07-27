"""Tests for reason node utility functions."""

from unittest.mock import Mock

import pytest
from resilient_result import Result

from cogency.nodes.reason import format_actions
from cogency.tools.base import BaseTool


class MockTool(BaseTool):
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


class TestFormatAgentResults:
    def test_format_actions_success(self):
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

    def test_format_actions_multiple_tools(self):
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

    def test_format_actions_no_execution_results(self):
        result = format_actions(None, [], [])
        assert result == ""

        # Test with execution results but no data
        empty_results = Result.ok(None)
        result = format_actions(empty_results, [], [])
        assert result == ""

    def test_format_actions_malformed_data(self):
        # Missing 'results' key
        bad_results = Result.ok({"summary": "test"})
        result = format_actions(bad_results, [], [])
        assert result == ""

        # Wrong data type
        bad_results = Result.ok("not a dict")
        result = format_actions(bad_results, [], [])
        assert result == ""

    def test_format_actions_tool_not_found(self):
        tool_calls = [{"name": "unknown_tool", "args": {}}]
        execution_results = Result.ok(
            {"results": [{"tool_name": "unknown_tool", "result": {"test": "data"}}]}
        )

        result = format_actions(execution_results, tool_calls, [])
        assert result == ""  # No matching tool found

    def test_format_actions_empty_result_data(self):
        search_tool = MockTool("search")
        tool_calls = [{"name": "search", "args": {}}]
        execution_results = Result.ok(
            {"results": [{"tool_name": "search", "result": {}}]}  # Empty result
        )

        result = format_actions(execution_results, tool_calls, [search_tool])
        assert result == "No results"  # format_agent handles empty data
