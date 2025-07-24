"""Consolidated parsing utilities - clean extraction from LLM responses."""

import json
import re
from typing import Any, Dict, List, Optional

from .results import ParseResult


def parse_json_result(response: str) -> ParseResult:
    """Extract JSON from LLM response - clean Result pattern.

    Handles:
    - Markdown code fences (```json and ```)
    - Proper brace matching for JSON objects
    - Graceful ParseResult.fail() on errors

    Args:
        response: Raw LLM response string

    Returns:
        ParseResult.ok(data) or ParseResult.fail(error)
    """
    if not response or not isinstance(response, str):
        return ParseResult.fail("Empty or invalid response")

    # Try direct JSON parsing first (fastest path)
    try:
        data = json.loads(response.strip())
        return ParseResult.ok(data)
    except json.JSONDecodeError:
        pass

    # Clean and extract JSON text from markdown
    json_text = _clean_json(response.strip())
    if not json_text:
        return ParseResult.fail("No JSON content found")

    try:
        data = json.loads(json_text)
        return ParseResult.ok(data)
    except json.JSONDecodeError as e:
        # Fallback: Use incremental parser to recover partial JSON
        try:
            for obj in _extract_json_stream(response):
                return ParseResult.ok(obj)  # Return first valid JSON object
        except Exception:
            pass

        return ParseResult.fail(f"JSON decode error: {str(e)}")


def _clean_json(response: str) -> str:
    """Extract JSON from markdown code blocks with brace matching."""
    # Use a more flexible regex to find JSON content
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
    if json_match:
        response = json_match.group(1).strip()

    # Extract JSON object with proper brace matching
    return _extract_json(response)


def _extract_json(text: str) -> str:
    """Extract JSON object with proper brace matching, accounting for strings."""
    start_idx = text.find("{")
    if start_idx == -1:
        return text

    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start_idx:], start_idx):
        if escape_next:
            escape_next = False
            continue

        if char == "\\" and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx : i + 1]

    return text


def _extract_json_stream(text: str):
    """Extract JSON objects incrementally from potentially corrupted text."""
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(text):
        # Skip whitespace and non-JSON characters
        while pos < len(text) and text[pos] not in "{[":
            pos += 1

        if pos >= len(text):
            break

        try:
            obj, index = decoder.raw_decode(text[pos:])
            yield obj
            pos += index
        except json.JSONDecodeError:
            pos += 1


def parse_tool_calls(json_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Extract tool calls from parsed JSON. Return None if no tool calls."""
    if not json_data:
        return None

    # Direct tool_calls array - clean format only
    tool_calls = json_data.get("tool_calls")

    # Limit tool calls to prevent JSON parsing issues
    if tool_calls:
        from cogency.constants import MAX_TOOL_CALLS_PER_ITERATION

        if len(tool_calls) > MAX_TOOL_CALLS_PER_ITERATION:
            # Truncate to max allowed tool calls
            return tool_calls[:MAX_TOOL_CALLS_PER_ITERATION]

    return tool_calls


def recover_json(response: str) -> ParseResult:
    """Extract JSON from broken LLM responses - Result pattern."""
    if not response:
        return ParseResult.fail("No response to recover")

    return parse_json_result(response)


def fallback_prompt(reason: str, system: str = None, schema: str = None) -> str:
    """Build fallback prompt when reasoning fails."""
    if schema:
        prompt = f"Reasoning failed: {reason}. Generate valid JSON matching schema: {schema}"
    else:
        prompt = f"Reasoning failed: {reason}. Provide helpful response based on context."

    return f"{system}\n\n{prompt}" if system else prompt


def fallback_response(error: Exception, schema: str = None) -> str:
    """Format error as JSON or text."""
    if schema:
        msg = str(error).replace('"', '\\"')
        return f'{{"error": "Technical issue", "details": "{msg}"}}'
    return f"Technical issue: {error}. Let me help based on our conversation."
