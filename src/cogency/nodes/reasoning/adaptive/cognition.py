"""Cognitive state management utilities."""

from typing import Any, Dict, List

FAST_MODE_MAX_HISTORY = 3
FAST_MODE_MAX_FAILURES = 2
DEEP_MODE_MAX_HISTORY = 10
DEEP_MODE_MAX_FAILURES = 5
ADAPTIVE_MODE_MAX_HISTORY = 5
ADAPTIVE_MODE_MAX_FAILURES = 3
FAST_MODE_REASONING_DEPTH = 1
DEEP_MODE_REASONING_DEPTH = 3
ADAPTIVE_MODE_REASONING_DEPTH = 2


def init_cognition(state, react_mode: str = "adaptive") -> Dict[str, Any]:
    """Initialize cognitive state with enhanced adaptive features."""
    default_state = {
        "approach_history": [],  # Methodologies tried (direct_search, synthesis, breakdown)
        "decision_history": [],  # Specific decisions taken (search_files, read_docs, analyze_code)
        "action_fingerprints": [],  # Concrete tool calls for loop detection (search(*.py), read(file.py))
        "failed_attempts": [],
        "current_approach": "initial",  # Current methodology
        "current_decision": "analyze",  # Current specific decision
        "last_tool_quality": "unknown",
        "react_mode": react_mode,
        "mode_switches": [],
        "complexity_indicators": {
            "query_length": len(str(state.get("query", "")).split()),
            "iteration_count": state.get("current_iteration", 0),
            "tool_failures": 0,
            "reasoning_depth": FAST_MODE_REASONING_DEPTH
            if react_mode == "fast"
            else DEEP_MODE_REASONING_DEPTH,
        },
        "cognitive_context": {
            "previous_mode": None,
            "switch_reasons": [],
            "performance_metrics": {"success_rate": 1.0, "avg_iterations": 1},
        },
    }

    # Set memory limits based on react_mode with enhanced parameters
    if react_mode == "fast":
        default_state["max_history"] = FAST_MODE_MAX_HISTORY  # Static FIFO
        default_state["max_failures"] = FAST_MODE_MAX_FAILURES
        default_state["context_window"] = "narrow"
        default_state["reasoning_depth"] = FAST_MODE_REASONING_DEPTH
    elif react_mode == "deep":
        default_state["max_history"] = DEEP_MODE_MAX_HISTORY  # Dynamic relevance
        default_state["max_failures"] = DEEP_MODE_MAX_FAILURES
        default_state["context_window"] = "broad"
        default_state["reasoning_depth"] = DEEP_MODE_REASONING_DEPTH
    else:  # adaptive - starts with fast, can escalate
        default_state["max_history"] = ADAPTIVE_MODE_MAX_HISTORY
        default_state["max_failures"] = ADAPTIVE_MODE_MAX_FAILURES
        default_state["context_window"] = "medium"
        default_state["reasoning_depth"] = ADAPTIVE_MODE_REASONING_DEPTH

    # Check if cognition already exists in state.flow
    if "cognition" not in state.flow:
        state.flow["cognition"] = default_state

    return state.flow["cognition"]


def update_cognition(
    cognition: Dict[str, Any],
    tool_calls: List[Any],
    current_approach: str,
    current_decision: str,
    action_fingerprint: str,
) -> None:
    """Update cognitive state with three-level tracking: approach, decision, and action fingerprint."""
    # Track methodologies/approaches for meta-learning
    cognition["approach_history"] = cognition.get("approach_history", [])
    cognition["approach_history"].append(current_approach)
    cognition["current_approach"] = current_approach

    # Track specific decisions for pattern detection
    cognition["decision_history"] = cognition.get("decision_history", [])
    cognition["decision_history"].append(current_decision)
    cognition["current_decision"] = current_decision

    # Track concrete tool calls for loop detection
    cognition["action_fingerprints"] = cognition.get("action_fingerprints", [])
    cognition["action_fingerprints"].append(action_fingerprint)

    # Adaptive memory management based on react_mode
    max_history = cognition.get("max_history", 5)
    react_mode = cognition.get("react_mode", "fast")

    if react_mode == "fast":
        # Simple FIFO truncation
        if len(cognition["approach_history"]) > max_history:
            cognition["approach_history"] = cognition["approach_history"][-max_history:]
        if len(cognition["decision_history"]) > max_history:
            cognition["decision_history"] = cognition["decision_history"][-max_history:]
        if len(cognition["action_fingerprints"]) > max_history:
            cognition["action_fingerprints"] = cognition["action_fingerprints"][-max_history:]
    else:
        # Deep mode: keep more history, but still limit for now (future enhancement: implement dynamic relevance scoring)
        if len(cognition["approach_history"]) > max_history:
            cognition["approach_history"] = cognition["approach_history"][-max_history:]
        if len(cognition["decision_history"]) > max_history:
            cognition["decision_history"] = cognition["decision_history"][-max_history:]
        if len(cognition["action_fingerprints"]) > max_history:
            cognition["action_fingerprints"] = cognition["action_fingerprints"][-max_history:]


def track_failure(
    cognition: Dict[str, Any],
    tool_calls: List[Any],
    tool_quality: str,
    current_iteration: int,
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
