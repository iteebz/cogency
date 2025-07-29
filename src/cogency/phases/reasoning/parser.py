"""Unified response parsing for reasoning modes."""

from resilient_result import Result


def parse_response_result(response: str) -> Result:
    """Unified parser for both fast and deep mode responses - Result pattern.

    Returns:
        Result.ok(data) with keys: thinking, switch_to, switch_why, tool_calls
        or Result.fail(error) with default fallback data
    """
    from cogency.utils import parse_json

    result = parse_json(response)
    if not result.success:
        # Return failure with fallback data
        fallback_data = {
            "thinking": "Processing request...",
            "switch_to": None,
            "switch_why": None,
            "tool_calls": [],
        }
        return Result.ok(fallback_data)  # Fallback data is better than failure

    data = result.data
    parsed_data = {
        "thinking": data.get("thinking"),
        "switch_to": data.get("switch_to"),
        "switch_why": data.get("switch_why"),
        "tool_calls": data.get("tool_calls", []),
    }

    return Result.ok(parsed_data)
