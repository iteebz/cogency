"""Test formatting utilities."""

import pytest

from cogency.utils.formatting import format_tool_params, summarize_tool_result, truncate


def test_truncate():
    """Test string truncation."""
    assert truncate("short", 30) == "short"
    assert (
        truncate("This is a very long text that should be truncated", 20)
        == "This is a very long..."
    )
    assert truncate("https://example.com/very/long/path", 20) == "example.com/..."
    assert truncate("/very/long/path/to/file.txt", 20) == ".../file.txt"
    assert truncate(None, 30) == ""


def test_format_tool_params():
    """Test parameter formatting."""
    assert format_tool_params({}) == ""
    assert format_tool_params({"query": "search term"}) == "(search term)"
    assert format_tool_params({"query": "search term", "limit": 10}) == "(search term)"
    assert format_tool_params({"count": 42}) == "(42)"

    # Long value truncation
    params = {"query": "this is a very long search query that should be truncated"}
    result = format_tool_params(params)
    assert len(result) <= 27
    assert result.startswith("(")
    assert result.endswith(")")


def test_summarize_tool_result():
    """Test result summarization."""
    assert summarize_tool_result(None) == "completed"
    assert summarize_tool_result({"error": "API key invalid"}) == "✗ API key invalid"
    assert summarize_tool_result({"result": "Task completed"}) == "Task completed"
    assert summarize_tool_result({"success": True}) == "✓ success"
    assert summarize_tool_result({"success": False}) == "✗ failed"
    assert summarize_tool_result(["item1", "item2", "item3"]) == "3 items"
    assert summarize_tool_result("Simple string") == "Simple string"

    # Long string truncation
    long_string = (
        "This is a very long string that should be truncated because it exceeds the maximum length"
    )
    result = summarize_tool_result(long_string)
    assert len(result) <= 60
    assert result.endswith("...")
