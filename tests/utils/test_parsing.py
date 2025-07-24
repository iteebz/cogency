"""Test parsing utilities for LLM response extraction."""

from unittest.mock import AsyncMock

import pytest

from cogency.utils.parsing import (
    _clean_json,
    _extract_json,
    parse_json,
    parse_tool_calls,
)


def test_parse_json():
    """Test JSON parsing from LLM responses using ParseResult."""
    # Basic JSON
    parse_result = parse_json('{"action": "respond", "message": "Hello"}')
    assert parse_result.success
    assert parse_result.data == {"action": "respond", "message": "Hello"}

    # Markdown fenced JSON
    markdown_json = """```json
    {"action": "use_tools", "reasoning": "Need to search"}
    ```"""
    parse_result = parse_json(markdown_json)
    assert parse_result.success
    assert parse_result.data == {"action": "use_tools", "reasoning": "Need to search"}

    # Malformed JSON without fallback
    parse_result = parse_json("invalid json")
    assert not parse_result.success
    assert parse_result.data is None
    assert parse_result.error is not None

    # JSON embedded in text
    parse_result = parse_json('Here is the JSON: {"action": "respond"} and extra text')
    assert parse_result.success
    assert parse_result.data == {"action": "respond"}

    # Invalid JSON without fallback
    parse_result = parse_json("invalid json")
    assert not parse_result.success
    assert parse_result.data is None
    assert parse_result.error is not None


def test_clean_json():
    """Test JSON cleaning utility."""
    # Remove markdown
    result = _clean_json('```json\n{"test": true}\n```')
    assert result == '{"test": true}'

    # Already clean
    result = _clean_json('{"clean": true}')
    assert result == '{"clean": true}'


def test_extract_json():
    """Test JSON extraction with brace matching."""
    # Simple object
    result = _extract_json('Data: {"key": "value"} extra')
    assert result == '{"key": "value"}'

    # Nested objects
    result = _extract_json('Response: {"outer": {"inner": "value"}} text')
    assert result == '{"outer": {"inner": "value"}}'

    # No JSON
    result = _extract_json("No JSON here")
    assert result == "No JSON here"


def test_parse_tool_calls():
    """Test tool call extraction."""
    # Valid tool calls
    json_data = {
        "tool_calls": [
            {"name": "search", "args": {"query": "test"}},
            {"name": "calculate", "args": {"expression": "2+2"}},
        ]
    }
    result = parse_tool_calls(json_data)
    assert len(result) == 2
    assert result[0]["name"] == "search"

    # No tool_calls key
    result = parse_tool_calls({"action": "respond", "message": "Hello"})
    assert result is None

    # Tool calls exist regardless of action - parser extracts them
    result = parse_tool_calls({"action": "respond", "tool_calls": [{"name": "test"}]})
    assert result == [{"name": "test"}]


# call_llm function was purged - testing unified parser instead
@pytest.mark.asyncio
async def test_json_parsing_with_llm_responses():
    """Test JSON parsing with typical LLM response formats."""
    # Test markdown wrapped JSON
    llm_response = """```json
    {"action": "use_tools", "tool_calls": [{"name": "search", "args": {"query": "test"}}]}
    ```"""
    parse_result = parse_json(llm_response)
    assert parse_result.success
    assert parse_result.data["action"] == "use_tools"
    assert len(parse_result.data["tool_calls"]) == 1

    # Test mixed content
    mixed_response = 'Here\'s my analysis: {"conclusion": "success"} and some extra text'
    parse_result = parse_json(mixed_response)
    assert parse_result.success
    assert parse_result.data["conclusion"] == "success"
