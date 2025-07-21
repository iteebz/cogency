"""Cognitive state management utilities."""

from typing import Any, Dict, List


def init_cognition(state, react_mode: str = "fast") -> Dict[str, Any]:
    """Initialize cognitive state with adaptive features based on react_mode."""
    default_state = {
        "strategy_history": [],
        "failed_attempts": [],
        "action_history": [],
        "current_strategy": "initial_approach",
        "last_tool_quality": "unknown",
        "react_mode": react_mode,
    }

    # Set memory limits based on react_mode
    if react_mode == "fast":
        default_state["max_history"] = 3  # Static FIFO
        default_state["max_failures"] = 5
    else:  # deep
        default_state["max_history"] = 10  # Dynamic relevance
        default_state["max_failures"] = 15

    # Check if cognition already exists in state.flow
    if "cognition" not in state.flow:
        state.flow["cognition"] = default_state

    return state.flow["cognition"]


def update_cognition(
    cognition: Dict[str, Any], tool_calls: List[Any], current_strategy: str, action_fingerprint: str
) -> None:
    """Update cognitive state with new action and strategy information."""
    # Track concrete action patterns for loop detection
    cognition["action_history"] = cognition.get("action_history", [])
    cognition["action_history"].append(action_fingerprint)

    # Track explicit strategy from LLM
    cognition["current_strategy"] = current_strategy
    cognition["strategy_history"] = cognition.get("strategy_history", [])
    cognition["strategy_history"].append(current_strategy)

    # Adaptive memory management based on react_mode
    max_history = cognition.get("max_history", 5)
    react_mode = cognition.get("react_mode", "fast")

    if react_mode == "fast":
        # Simple FIFO truncation
        if len(cognition["action_history"]) > max_history:
            cognition["action_history"] = cognition["action_history"][-max_history:]
        if len(cognition["strategy_history"]) > max_history:
            cognition["strategy_history"] = cognition["strategy_history"][-max_history:]
    else:
        # Deep mode: keep more history, but still limit for now (future enhancement: implement dynamic relevance scoring)
        if len(cognition["action_history"]) > max_history:
            cognition["action_history"] = cognition["action_history"][-max_history:]
        if len(cognition["strategy_history"]) > max_history:
            cognition["strategy_history"] = cognition["strategy_history"][-max_history:]


def track_failure(
    cognition: Dict[str, Any], tool_calls: List[Any], tool_quality: str, current_iteration: int
) -> None:
    """Track failed attempts for loop prevention."""
    for call in tool_calls:
        cognition["failed_attempts"].append(
            {
                "tool": getattr(call, "name", "unknown"),
                "args": getattr(call, "args", {}),
                "reason": tool_quality,
                "iteration": current_iteration,
            }
        )

    # Adaptive failure tracking based on react_mode
    max_failures = cognition.get("max_failures", 10)
    if len(cognition["failed_attempts"]) > max_failures:
        cognition["failed_attempts"] = cognition["failed_attempts"][-max_failures:]


def summarize_attempts(failed_attempts: List[Dict[str, Any]]) -> str:
    """Create a summary of previous failed attempts."""
    if not failed_attempts:
        return "No previous failed attempts"

    return (
        f"Previous failed attempts: {len(failed_attempts)} attempts failed. "
        f"Last failures: "
        + ", ".join(
            [
                f"{attempt['tool']}({attempt.get('reason', 'unknown')})"
                for attempt in failed_attempts[-3:]
            ]
        )
    )
