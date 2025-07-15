"""NO BULLSHIT parsing tests - only test real bugs that break shit."""
import pytest
from cogency.utils.parsing import parse_tool_args, extract_tool_call


def test_parse_tool_args_with_quotes():
    """Test parsing args with quoted strings - REAL BUG."""
    # This should NOT crash with ValueError
    raw_args = "content='my favorite color is blue', tags=['personal', 'work']"
    result = parse_tool_args(raw_args)
    
    assert "content" in result
    assert result["content"] == "my favorite color is blue"


def test_parse_tool_args_with_lists():
    """Test parsing list arguments - REAL BUG."""
    raw_args = "tags=['tag1', 'tag2']"
    result = parse_tool_args(raw_args)
    
    assert "tags" in result
    assert isinstance(result["tags"], list)
    assert "tag1" in result["tags"]


def test_extract_tool_call_with_memorize():
    """Test extracting memorize tool calls - REAL BUG."""
    content = """I need to memorize this.

TOOL_CALL: memorize(content='blue is my favorite color', tags=['personal'])
"""
    result = extract_tool_call(content)
    
    assert result is not None
    tool_name, tool_args = result
    assert tool_name == "memorize"
    assert "raw_args" in tool_args


def test_parse_simple_args_still_works():
    """Ensure simple parsing still works."""
    raw_args = "x=5, y=10"
    result = parse_tool_args(raw_args)
    
    assert result["x"] == 5
    assert result["y"] == 10