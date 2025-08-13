"""Test parsing utilities for LLM response extraction."""

import pytest

from cogency.utils.parsing import (
    _clean_json,
    _extract_json,
    _extract_json_stream,
    _extract_patterns,
    _parse_json,
    _parse_tool_calls,
)


def test_json():
    # Basic JSON
    parse_result = _parse_json('{"action": "respond", "message": "Hello"}')
    assert parse_result.success
    assert parse_result.unwrap() == {"action": "respond", "message": "Hello"}

    # Markdown fenced JSON
    markdown_json = """```json
    {"action": "use_tools", "reasoning": "Need to search"}
    ```"""
    parse_result = _parse_json(markdown_json)
    assert parse_result.success
    assert parse_result.unwrap() == {"action": "use_tools", "reasoning": "Need to search"}

    # Malformed JSON without fallback
    parse_result = _parse_json("invalid json")
    assert not parse_result.success
    assert parse_result.failure
    assert parse_result.error is not None

    # JSON embedded in text
    parse_result = _parse_json('Here is the JSON: {"action": "respond"} and extra text')
    assert parse_result.success
    assert parse_result.unwrap() == {"action": "respond"}

    # Invalid JSON without fallback
    parse_result = _parse_json("invalid json")
    assert not parse_result.success
    assert parse_result.failure
    assert parse_result.error is not None


def test_clean():
    # Remove markdown
    result = _clean_json('```json\n{"test": true}\n```')
    assert result == '{"test": true}'

    # Already clean
    result = _clean_json('{"clean": true}')
    assert result == '{"clean": true}'


def test_extract():
    # Simple object
    result = _extract_json('Data: {"key": "value"} extra')
    assert result == '{"key": "value"}'

    # Nested objects
    result = _extract_json('Response: {"outer": {"inner": "value"}} text')
    assert result == '{"outer": {"inner": "value"}}'

    # No JSON
    result = _extract_json("No JSON here")
    assert result == "No JSON here"


def test_calls():
    # Valid tool calls
    json_data = {
        "tool_calls": [
            {"name": "search", "args": {"query": "test"}},
            {"name": "calculate", "args": {"expression": "2+2"}},
        ]
    }
    result = _parse_tool_calls(json_data)
    assert len(result) == 2
    assert result[0]["name"] == "search"

    # No tool_calls key
    result = _parse_tool_calls({"action": "respond", "message": "Hello"})
    assert result is None

    # Tool calls exist regardless of action - parser extracts them
    result = _parse_tool_calls({"action": "respond", "tool_calls": [{"name": "test"}]})
    assert result == [{"name": "test"}]


# call_llm function was purged - testing unified parser instead
@pytest.mark.asyncio
async def test_llm():
    # Test markdown wrapped JSON
    response = """```json
    {"action": "use_tools", "tool_calls": [{"name": "search", "args": {"query": "test"}}]}
    ```"""
    parse_result = _parse_json(response)
    assert parse_result.success
    assert parse_result.unwrap()["action"] == "use_tools"
    assert len(parse_result.unwrap()["tool_calls"]) == 1

    # Test mixed content
    mixed_response = 'Here\'s my analysis: {"conclusion": "success"} and some extra text'
    parse_result = _parse_json(mixed_response)
    assert parse_result.success
    assert parse_result.unwrap()["conclusion"] == "success"


def test_multi():
    # Multiple JSON objects in sequence - should return FIRST only
    multi_json = (
        """{"thinking": "step1", "tool_calls": []} {"thinking": "step2", "tool_calls": []}"""
    )

    objects = list(_extract_json_stream(multi_json))

    assert len(objects) == 1  # Should stop after first object
    assert objects[0]["thinking"] == "step1"


def test_patterns():
    # Pattern 1: JSON with explanation text
    response1 = 'Here is my response: {"thinking": "analysis", "tool_calls": []}'
    extracted = _extract_patterns(response1)
    assert extracted == '{"thinking": "analysis", "tool_calls": []}'

    # Pattern 2: JSON with trailing text
    response2 = '{"thinking": "plan", "tool_calls": []} and some extra explanation'
    extracted = _extract_patterns(response2)
    assert extracted == '{"thinking": "plan", "tool_calls": []}'

    # Pattern 3: No valid JSON structure
    response3 = "Just text with no JSON structure"
    extracted = _extract_patterns(response3)
    assert extracted is None
