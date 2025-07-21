"""Cognitive state management utilities."""
from typing import Dict, Any, List


def initialize_cognitive_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize cognitive state with default values."""
    return state.setdefault("cognitive_state", {
        "strategy_history": [],
        "failed_attempts": [],
        "action_history": [],
        "current_strategy": "initial_approach",
        "last_tool_quality": "unknown"
    })


def update_cognitive_state(
    cognitive_state: Dict[str, Any], 
    tool_calls: List[Any], 
    current_strategy: str,
    action_fingerprint: str
) -> None:
    """Update cognitive state with new action and strategy information."""
    # Track concrete action patterns for loop detection
    cognitive_state["action_history"] = cognitive_state.get("action_history", [])
    cognitive_state["action_history"].append(action_fingerprint)
    
    # Track explicit strategy from LLM
    cognitive_state["current_strategy"] = current_strategy
    cognitive_state["strategy_history"] = cognitive_state.get("strategy_history", [])
    cognitive_state["strategy_history"].append(current_strategy)
    
    # Limit histories to prevent memory bloat
    if len(cognitive_state["action_history"]) > 10:
        cognitive_state["action_history"] = cognitive_state["action_history"][-10:]
    if len(cognitive_state["strategy_history"]) > 5:
        cognitive_state["strategy_history"] = cognitive_state["strategy_history"][-5:]


def track_failed_attempt(
    cognitive_state: Dict[str, Any], 
    tool_calls: List[Any], 
    tool_quality: str, 
    current_iteration: int
) -> None:
    """Track failed attempts for loop prevention."""
    for call in tool_calls:
        cognitive_state["failed_attempts"].append({
            "tool": getattr(call, 'name', 'unknown'),
            "args": getattr(call, 'args', {}),
            "reason": tool_quality,
            "iteration": current_iteration
        })
    
    # Limit failed attempts history to prevent memory bloat
    if len(cognitive_state["failed_attempts"]) > 10:
        cognitive_state["failed_attempts"] = cognitive_state["failed_attempts"][-10:]


def create_attempts_summary(failed_attempts: List[Dict[str, Any]]) -> str:
    """Create a summary of previous failed attempts."""
    if not failed_attempts:
        return "No previous failed attempts"
    
    return (f"Previous failed attempts: {len(failed_attempts)} attempts failed. "
            f"Last failures: " + 
            ", ".join([f"{attempt['tool']}({attempt.get('reason', 'unknown')})" 
                      for attempt in failed_attempts[-3:]]))