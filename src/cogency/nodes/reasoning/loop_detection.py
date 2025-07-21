"""Action loop detection and prevention."""
from typing import List, Any, Dict


def create_action_fingerprint(tool_calls: List[Any]) -> str:
    """Create a fingerprint of tool calls for loop detection."""
    if not tool_calls:
        return "no_action"
    
    # Create simple fingerprint from tool names and key args
    fingerprints = []
    for call in tool_calls:
        tool_name = getattr(call, 'name', 'unknown')
        args = getattr(call, 'args', {})
        
        # Create fingerprint from tool + relevant args
        if isinstance(args, dict):
            key_args = {k: v for k, v in args.items() if k in ['query', 'url', 'code', 'content']}
            fingerprint = f"{tool_name}:{hash(str(sorted(key_args.items())))}"
        else:
            fingerprint = f"{tool_name}:{hash(str(args))}"
        
        fingerprints.append(fingerprint)
    
    return "|".join(fingerprints)


def detect_action_loop(cognitive_state: Dict[str, Any]) -> bool:
    """Detect if agent is stuck in an action loop."""
    action_history = cognitive_state.get("action_history", [])
    
    if len(action_history) < 3:
        return False
    
    # Check for repeated identical actions
    recent_actions = action_history[-3:]
    if len(set(recent_actions)) == 1:  # All 3 recent actions are identical
        return True
    
    # Check for alternating pattern (A-B-A)
    if len(action_history) >= 3:
        if action_history[-1] == action_history[-3] and action_history[-1] != action_history[-2]:
            return True
    
    return False


def detect_fast_mode_loop(cognitive_state: Dict[str, Any]) -> bool:
    """Lightweight loop detection for fast mode - lower threshold."""
    action_history = cognitive_state.get("action_history", [])
    
    # Fast mode: detect loops earlier with just 2 actions
    if len(action_history) < 2:
        return False
    
    # Check for immediate repetition (A-A)
    recent_actions = action_history[-2:]
    if recent_actions[0] == recent_actions[1]:
        return True
    
    # Check for simple alternating pattern with lower threshold
    if len(action_history) >= 2:
        # If we see the same action twice in last 2, it's a loop in fast mode
        if action_history[-1] == action_history[-2]:
            return True
    
    return False