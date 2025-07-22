"""Action loop detection and prevention."""

from typing import Any, Dict, List


def action_fingerprint(tool_calls: List[Any]) -> str:
    """Create a fingerprint of tool calls for loop detection."""
    if not tool_calls:
        return "no_action"

    # Create simple fingerprint from tool names and key args
    fingerprints = []
    for call in tool_calls:
        tool_name = call.get("name", "unknown")
        args = call.get("args", {})

        # Create fingerprint from tool + relevant args
        if isinstance(args, dict):
            key_args = {k: v for k, v in args.items() if k in ["query", "url", "code", "content", "operation", "command", "filename", "action"]}
            fingerprint = f"{tool_name}:{hash(str(sorted(key_args.items())))}"
        else:
            fingerprint = f"{tool_name}:{hash(str(args))}"

        fingerprints.append(fingerprint)

    return "|".join(fingerprints)


def detect_loop(cognition: Dict[str, Any]) -> bool:
    """Detect if agent is stuck in an action loop."""
    action_fingerprints = cognition.get("action_fingerprints", [])

    if len(action_fingerprints) < 3:
        return False

    # Check for repeated identical actions
    recent_actions = action_fingerprints[-3:]
    if len(set(recent_actions)) == 1:  # All 3 recent actions are identical
        return True

    # Check for alternating pattern (A-B-A)
    return (
        len(action_fingerprints) >= 3
        and action_fingerprints[-1] == action_fingerprints[-3]
        and action_fingerprints[-1] != action_fingerprints[-2]
    )


def detect_fast_loop(cognition: Dict[str, Any]) -> bool:
    """Lightweight loop detection for fast mode - lower threshold."""
    action_fingerprints = cognition.get("action_fingerprints", [])

    # Fast mode: detect loops earlier with just 2 actions
    if len(action_fingerprints) < 2:
        return False

    # Check for immediate repetition (A-A)
    recent_actions = action_fingerprints[-2:]
    if recent_actions[0] == recent_actions[1]:
        return True
