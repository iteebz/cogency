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

    # Clean and extract JSON text
    json_text = _clean_json(response.strip())
    if not json_text:
        return ParseResult.fail("No JSON content found")

    try:
        data = json.loads(json_text)
        return ParseResult.ok(data)
    except json.JSONDecodeError as e:
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
    """Extract JSON object with proper brace matching."""
    start_idx = text.find("{")
    if start_idx == -1:
        return text

    brace_count = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return text[start_idx : i + 1]

    return text


def parse_tool_calls(json_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Extract tool calls from parsed JSON. Return None if no tool calls."""
    if not json_data:
        return None

    # Direct tool_calls array - clean format only
    return json_data.get("tool_calls")


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
