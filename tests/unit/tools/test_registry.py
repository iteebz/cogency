"""Tool registry tests."""

import pytest

from cogency.tools.base import Tool
from cogency.tools.files import Files
from cogency.tools.registry import _setup_tools


def test_setup_tools_valid_list():
    """Test _setup_tools with valid tool instances."""
    files_tool = Files()
    tools = [files_tool]

    result = _setup_tools(tools, None)

    assert len(result) == 1
    assert result[0] is files_tool


def test_setup_tools_empty_list():
    """Test _setup_tools with empty list."""
    result = _setup_tools([], None)
    assert result == []


def test_setup_tools_none_raises():
    """Test _setup_tools raises on None."""
    with pytest.raises(ValueError, match="tools must be explicitly specified"):
        _setup_tools(None, None)


def test_setup_tools_string_raises():
    """Test _setup_tools raises on string."""
    with pytest.raises(ValueError, match="Invalid tools value"):
        _setup_tools("search", None)


def test_setup_tools_invalid_type_raises():
    """Test _setup_tools raises on non-Tool instances."""
    with pytest.raises(ValueError, match="Invalid tool type"):
        _setup_tools(["not_a_tool"], None)


def test_register():
    from cogency.tools.registry import get_tools

    # Test basic registry functionality
    tools = get_tools()
    assert isinstance(tools, list)
