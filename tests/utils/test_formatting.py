"""Test formatting utilities for consistent display."""

import pytest

from cogency.utils.formatting import format_tool_params, summarize_tool_result, truncate


class TestFormatting:
    """Test formatting utilities for consistent display."""

    @pytest.mark.parametrize(
        "input_text,max_length,expected",
        [
            # Core truncation cases
            ("short", 30, "short"),  # Short text (no truncation)
            (
                "This is a very long text that should be truncated",
                20,
                "This is a very long...",
            ),  # Basic truncation
            ("https://example.com/very/long/path", 20, "example.com/..."),  # URL truncation
            ("/very/long/path/to/file.txt", 20, ".../file.txt"),  # Path truncation
            (None, 30, ""),  # Edge case: None input
        ],
    )
    def test_truncate(self, input_text, max_length, expected):
        """Test string truncation with representative cases."""
        result = truncate(input_text, max_length)
        assert result == expected

    @pytest.mark.parametrize(
        "params,expected",
        [
            # Core parameter formatting cases
            ({}, ""),  # Empty params
            ({"query": "search term"}, "(search term)"),  # Basic case
            (
                {"query": "search term", "limit": 10},
                "(search term)",
            ),  # Multiple params (uses first)
            ({"count": 42}, "(42)"),  # Numeric value
        ],
    )
    def test_format_tool_params(self, params, expected):
        """Test parameter formatting with representative cases."""
        result = format_tool_params(params)
        assert result == expected

    def test_format_tool_params_special_cases(self):
        """Test special cases for parameter formatting."""
        # Long value truncation
        params = {"query": "this is a very long search query that should be truncated"}
        result = format_tool_params(params)
        assert len(result) <= 27  # 25 + 2 for parentheses
        assert result.startswith("(")
        assert result.endswith(")")

        # Complex value
        params = {"data": {"nested": "value"}}
        result = format_tool_params(params)
        assert result.startswith("(")
        assert "nested" in result or "value" in result

    @pytest.mark.parametrize(
        "result_data,expected",
        [
            # Core result summarization cases
            (None, "completed"),  # None input
            ({"error": "API key invalid"}, "✗ API key invalid"),  # Error case
            ({"result": "Task completed"}, "Task completed"),  # Result case
            ({"success": True}, "✓ success"),  # Success flag
            ({"success": False}, "✗ failed"),  # Failure flag
            (["item1", "item2", "item3"], "3 items"),  # List handling
            ("Simple string", "Simple string"),  # String passthrough
        ],
    )
    def test_summarize_tool_result(self, result_data, expected):
        """Test result summarization with representative cases."""
        result = summarize_tool_result(result_data)
        assert result == expected

    def test_summarize_tool_result_edge_cases(self):
        """Test edge cases for result summarization."""
        # Long string truncation
        long_string = "This is a very long string that should be truncated because it exceeds the maximum length"
        result = summarize_tool_result(long_string)
        assert len(result) <= 60
        assert result.endswith("...")

        # Exception handling
        class BreakingObject:
            def __str__(self):
                raise Exception("Cannot convert to string")

            def __getitem__(self, key):
                raise Exception("Cannot access items")

        result = summarize_tool_result(BreakingObject())
        assert result == "completed"  # Falls back to default
