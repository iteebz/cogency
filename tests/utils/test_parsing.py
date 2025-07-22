"""Test parsing utilities for LLM response extraction."""

from unittest.mock import AsyncMock

import pytest

from cogency.nodes.reasoning.fast import parse_fast_mode
from cogency.utils.parsing import (
    _clean_json,
    _extract_json,
    call_llm,
    parse_json,
    parse_tool_calls,
)


def test_parse_json():
    """Test JSON parsing from LLM responses."""
    # Basic JSON
    result = parse_json('{"action": "respond", "message": "Hello"}')
    assert result == {"action": "respond", "message": "Hello"}

    # Markdown fenced JSON
    markdown_json = """```json
    {"action": "use_tools", "reasoning": "Need to search"}
    ```"""
    result = parse_json(markdown_json)
    assert result == {"action": "use_tools", "reasoning": "Need to search"}

    # Malformed JSON with fallback
    result = parse_json("invalid json", fallback={"error": "parsing_failed"})
    assert result == {"error": "parsing_failed"}

    # JSON embedded in text
    result = parse_json('Here is the JSON: {"action": "respond"} and extra text')
    assert result == {"action": "respond"}


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

    # Invalid cases
    result = parse_tool_calls({"action": "respond", "message": "Hello"})
    assert result is None

    # Wrong action type
    result = parse_tool_calls({"action": "respond", "tool_calls": [{"name": "test"}]})
    assert result is None


def test_parse_fast_thinking():
    """Test fast thinking extraction."""
    # JSON thinking
    result = parse_fast_mode('{"thinking": "Need to search", "action": "use_tools"}')
    assert result["thinking"] == "Need to search"

    # No thinking (uses default when no JSON)
    result = parse_fast_mode("invalid json")
    assert result["thinking"] == "Analyzing the request and determining approach"


@pytest.mark.asyncio
async def test_call_llm():
    """Test LLM calling utility."""
    # Mock LLM
    mock_llm = AsyncMock()
    mock_llm.run.return_value = "Test response"

    messages = [{"role": "user", "content": "Hello"}]
    result = await call_llm(mock_llm, messages)

    assert result == "Test response"
    mock_llm.run.assert_called_once_with(messages)


@pytest.mark.asyncio
async def test_call_llm_error_handling():
    """Test LLM error handling."""
    # Mock LLM that raises exception
    mock_llm = AsyncMock()
    mock_llm.run.side_effect = Exception("API Error")

    messages = [{"role": "user", "content": "Hello"}]

    # Should raise the exception
    with pytest.raises(Exception):
        await call_llm(mock_llm, messages)
