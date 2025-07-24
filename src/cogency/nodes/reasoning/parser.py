"""Unified response parsing for reasoning modes."""

from typing import Optional

from cogency.utils.results import ParseResult


def parse_response_result(response: str) -> ParseResult:
    """Unified parser for both fast and deep mode responses - Result pattern.

    Returns:
        ParseResult.ok(data) with keys: thinking, switch_to, switch_why, tool_calls
        or ParseResult.fail(error) with default fallback data
    """
    from cogency.utils.parsing import parse_json

    result = parse_json(response)
    if not result.success:
        # Return failure with fallback data
        fallback_data = {
            "thinking": "Processing request...",
            "switch_to": None,
            "switch_why": None,
            "tool_calls": [],
        }
        return ParseResult.ok_with_error(fallback_data, f"Parse failed: {result.error}")

    data = result.data
    parsed_data = {
        "thinking": data.get("thinking") or data.get("reasoning"),  # Handle both field names
        "switch_to": data.get("switch_to"),
        "switch_why": data.get("switch_why")
        or data.get("switch_reason"),  # Handle both field names
        "tool_calls": data.get("tool_calls", []),
    }

    return ParseResult.ok(parsed_data)


def format_thinking(thinking: Optional[str], mode: str = "fast") -> str:
    """Format thinking content for display."""
    if not thinking:
        return "Processing request..."

    # Add mode-specific emoji prefixes for visual distinction
    if mode == "deep":
        return f"🧠 {thinking}"
    else:
        return f"💭 {thinking}"
