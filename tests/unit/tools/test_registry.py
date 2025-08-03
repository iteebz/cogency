"""Tool registry tests."""

import os
from unittest.mock import MagicMock, patch

import pytest

from cogency.tools.base import Tool
from cogency.tools.files import Files
from cogency.tools.http import HTTP
from cogency.tools.registry import (
    _get_tool,
    _resolve_tool_list,
    _setup_tools,
)


def test_register():
    from cogency.tools.registry import get_tools

    tools = get_tools()
    tool_names = [t.name for t in tools]

    assert "files" in tool_names


def test_discover():
    from cogency.tools.registry import get_tools

    tools = get_tools()

    for tool in tools:
        assert isinstance(tool, Tool)
        assert hasattr(tool, "name") and tool.name
        assert hasattr(tool, "description") and tool.description

        schema = tool.schema
        assert len(schema) > 0

        examples = tool.examples
        assert len(examples) > 0


def test_setup_string_names():
    """Test that string tool names resolve to tool instances."""
    result = _setup_tools(["search", "files"], None)

    assert len(result) == 2
    assert all(isinstance(tool, Tool) for tool in result)

    tool_names = [tool.name for tool in result]
    assert "search" in tool_names
    assert "files" in tool_names


def test_setup_mixed_list():
    """Test that mixed string/instance lists work."""
    http_instance = HTTP()
    result = _setup_tools(["search", http_instance], None)

    assert len(result) == 2
    assert all(isinstance(tool, Tool) for tool in result)

    # Check that HTTP instance is preserved
    assert http_instance in result


def test_setup_all():
    """Test that 'all' still works."""
    from cogency.tools.registry import ToolRegistry

    result = _setup_tools("all", None)
    expected = ToolRegistry.get_tools()

    assert len(result) == len(expected)
    assert all(isinstance(tool, Tool) for tool in result)


def test_setup_empty_list():
    """Test that empty list returns empty list."""
    result = _setup_tools([], None)
    assert result == []


def test_setup_none_raises():
    """Test that None raises ValueError."""
    with pytest.raises(ValueError, match="tools must be explicitly specified"):
        _setup_tools(None, None)


def test_setup_invalid_string_raises():
    """Test that invalid string raises ValueError."""
    with pytest.raises(ValueError, match="Invalid tools value"):
        _setup_tools("invalid", None)


def test_get_tool_valid():
    """Test resolving valid tool names."""
    search_tool = _get_tool("search")
    assert search_tool is not None
    assert search_tool.name == "search"

    files_tool = _get_tool("files")
    assert files_tool is not None
    assert files_tool.name == "files"


def test_get_tool_case_insensitive():
    """Test that tool name resolution is case insensitive."""
    search_tool = _get_tool("SEARCH")
    assert search_tool is not None
    assert search_tool.name == "search"


def test_get_tool_invalid():
    """Test that invalid tool names return None."""
    result = _get_tool("nonexistent")
    assert result is None


def test_resolve_strings():
    """Test resolving list of strings."""
    result = _resolve_tool_list(["search", "files"])

    assert len(result) == 2
    assert all(isinstance(tool, Tool) for tool in result)

    tool_names = [tool.name for tool in result]
    assert "search" in tool_names
    assert "files" in tool_names


def test_resolve_mixed():
    """Test resolving mixed string/instance list."""
    http_instance = HTTP()
    result = _resolve_tool_list(["search", http_instance])

    assert len(result) == 2
    assert http_instance in result

    # Find the search tool
    search_tool = next(tool for tool in result if tool.name == "search")
    assert search_tool is not None


def test_resolve_invalid_string():
    """Test that invalid strings are skipped with warning."""
    with patch("cogency.tools.registry.logger") as mock_logger:
        result = _resolve_tool_list(["search", "nonexistent", "files"])

        # Should get 2 valid tools
        assert len(result) == 2
        tool_names = [tool.name for tool in result]
        assert "search" in tool_names
        assert "files" in tool_names

        # Should log warning about invalid tool
        mock_logger.warning.assert_called_with("Unknown tool name: nonexistent")


def test_resolve_invalid_type():
    """Test that invalid types are skipped with warning."""
    with patch("cogency.tools.registry.logger") as mock_logger:
        result = _resolve_tool_list(["search", 123, Files()])

        # Should get 2 valid tools
        assert len(result) == 2

        # Should log warning about invalid type
        mock_logger.warning.assert_called_with("Invalid tool type: <class 'int'>")


def test_all_tools_resolvable():
    """Test that all tools in the mapping can be resolved."""
    tool_names = ["files", "http", "scrape", "search", "shell"]

    for name in tool_names:
        tool = _get_tool(name)
        assert tool is not None, f"Failed to resolve tool: {name}"
        assert tool.name == name
