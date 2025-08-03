"""Tool result formatting and failure collection."""

from typing import Dict, Optional

from cogency.state import AgentState


def collect_failures(state: AgentState) -> Optional[Dict[str, str]]:
    """Collect all failure scenarios into unified dict."""
    failures = {}

    # Check for stop reason (reasoning failures)
    if state.execution.stop_reason:
        user_error_message = getattr(
            state, "user_error_message", "I encountered an issue but will try to help."
        )
        failures["reasoning"] = user_error_message
        return failures

    # Check for tool failures in completed calls
    for result in state.execution.completed_calls:
        if (
            "result" in result
            and result["result"]
            and hasattr(result["result"], "success")
            and not result["result"].success
        ):
            failures[result["name"]] = str(result["result"].error) or "Tool execution failed"

    return failures if failures else None


def format_tool_results(state: AgentState) -> Optional[str]:
    """Extract and format tool results for response context."""
    if not state.execution.completed_calls:
        return None

    # Format completed tool results
    successful_results = [
        result for result in state.execution.completed_calls[:5] if "result" in result
    ]

    if not successful_results:
        return None

    return "\n".join(
        [
            f"• {result['name']}: {str(result['result'] or 'no result')[:200]}..."
            for result in successful_results
        ]
    )
