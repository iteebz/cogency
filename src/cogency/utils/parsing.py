"""Consolidated parsing utilities - clean extraction from LLM responses."""

import json
import re
from typing import Any, Dict, List, Optional


async def call_llm(llm, messages: List[Dict[str, str]]) -> str:
    """Call LLM and return response. That's it."""
    return await llm.run(messages)


def parse_json(response: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract JSON from LLM response with markdown cleaning and error handling.

    Handles:
    - Markdown code fences (```json and ```)
    - Proper brace matching for JSON objects
    - Graceful fallback on parsing errors

    Args:
        response: Raw LLM response string
        fallback: Default dict to return on parsing errors

    Returns:
        Parsed JSON dict or fallback
    """
    if not response or not isinstance(response, str):
        return fallback or {}

    # Clean and extract JSON text
    json_text = _clean_json(response.strip())
    if not json_text:
        print(f"parse_json: json_text is empty, returning fallback: {fallback or {}}")
        return fallback or {}

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return fallback or {}


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


# This function is already defined above


def parse_tool_calls(json_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Extract tool calls from parsed JSON. Return None if no tool calls."""
    if not json_data:
        return None

    # New format: direct tool_calls array
    if "tool_calls" in json_data:
        # Check if action is not "use_tools" (legacy format check)
        action = json_data.get("action")
        if action is not None and action != "use_tools":
            return None
        return json_data.get("tool_calls", [])

    # Legacy format support
    action = json_data.get("action")
    if action == "use_tools":
        return json_data.get("tool_calls", [])
    return None
