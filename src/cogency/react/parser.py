"""Parser: JSON response parsing and enforcement."""

import json
from typing import Any


def parse_json_response(response: str, max_retries: int = 3) -> dict[str, Any]:
    """Parse JSON response with enforcement and fallbacks."""
    cleaned = extract_json(response)

    try:
        parsed = json.loads(cleaned)
        if "action" not in parsed and "final_answer" not in parsed:
            raise json.JSONDecodeError("Missing required fields", cleaned, 0)
        return parsed
    except json.JSONDecodeError as e:
        # Emergency fallback
        return {
            "reasoning": f"JSON parsing failed: {str(e)}",
            "action": {"type": "final_answer"},
            "final_answer": f"Error: Could not parse response - {str(e)}",
        }


def extract_json(response: str) -> str:
    """Extract JSON from response text."""
    response = response.strip()

    # Remove markdown code blocks
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]

    response = response.strip()

    # Find JSON object boundaries
    start = response.find("{")
    if start == -1:
        return response

    # Find matching closing brace
    brace_count = 0
    for i, char in enumerate(response[start:], start):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return response[start : i + 1]

    return response
