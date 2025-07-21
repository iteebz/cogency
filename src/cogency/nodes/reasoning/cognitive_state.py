"""Cognitive state management utilities."""
from typing import Dict, Any, List


def initialize_cognitive_state(state: Dict[str, Any], react_mode: str = "fast") -> Dict[str, Any]:
    """Initialize cognitive state with adaptive features based on react_mode."""
    default_state = {
        "strategy_history": [],
        "failed_attempts": [],
        "action_history": [],
        "current_strategy": "initial_approach",
        "last_tool_quality": "unknown",
        "react_mode": react_mode
    }
    
    # Set memory limits based on react_mode
    if react_mode == "fast":
        default_state["max_history"] = 3  # Static FIFO
        default_state["max_failures"] = 5
    else:  # deep
        default_state["max_history"] = 10  # Dynamic relevance
        default_state["max_failures"] = 15
        
    return state.setdefault("cognitive_state", default_state)


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
    
    # Adaptive memory management based on react_mode
    max_history = cognitive_state.get("max_history", 5)
    react_mode = cognitive_state.get("react_mode", "fast")
    
    if react_mode == "fast":
        # Simple FIFO truncation
        if len(cognitive_state["action_history"]) > max_history:
            cognitive_state["action_history"] = cognitive_state["action_history"][-max_history:]
        if len(cognitive_state["strategy_history"]) > max_history:
            cognitive_state["strategy_history"] = cognitive_state["strategy_history"][-max_history:]
    else:
        # Deep mode: keep more history, but still limit for now (dynamic relevance scoring TODO)
        if len(cognitive_state["action_history"]) > max_history:
            cognitive_state["action_history"] = cognitive_state["action_history"][-max_history:]
        if len(cognitive_state["strategy_history"]) > max_history:
            cognitive_state["strategy_history"] = cognitive_state["strategy_history"][-max_history:]


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
    
    # Adaptive failure tracking based on react_mode  
    max_failures = cognitive_state.get("max_failures", 10)
    if len(cognitive_state["failed_attempts"]) > max_failures:
        cognitive_state["failed_attempts"] = cognitive_state["failed_attempts"][-max_failures:]


def create_attempts_summary(failed_attempts: List[Dict[str, Any]]) -> str:
    """Create a summary of previous failed attempts."""
    if not failed_attempts:
        return "No previous failed attempts"
    
    return (f"Previous failed attempts: {len(failed_attempts)} attempts failed. "
            f"Last failures: " + 
            ", ".join([f"{attempt['tool']}({attempt.get('reason', 'unknown')})" 
                      for attempt in failed_attempts[-3:]]))