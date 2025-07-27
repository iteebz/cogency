"""Action loop detection and prevention."""

from typing import Any, List



def action_fingerprint(tool_calls: List[Any]) -> str:
    """Create readable fingerprint of tool calls for loop detection."""
    if not tool_calls:
        return "no_action"

    parts = []
    for call in tool_calls:
        name = call.get("name", "unknown")
        args = call.get("args", {})
        
        # Extract key parameters for readable fingerprint
        if isinstance(args, dict):
            key_args = {k: v for k, v in args.items() if k in ["query", "url", "filename", "command"]}
            if key_args:
                args_str = ",".join(f"{k}={v}" for k, v in key_args.items())
                parts.append(f"{name}({args_str})")
            else:
                parts.append(name)
        else:
            parts.append(f"{name}({args})")
    
    return "|".join(parts)


def detect_loop(state) -> bool:
    """Detect if agent is stuck in an iteration loop (deep mode)."""
    iteration_entries = state.iterations
    min_actions = 3

    if len(iteration_entries) < min_actions:
        return False

    # Extract fingerprints from iteration entries
    fingerprints = [
        entry.get("fingerprint", "unknown")
        for entry in iteration_entries
        if entry and isinstance(entry, dict)
    ]

    # Check for repeated identical iterations
    recent_iterations = fingerprints[-min_actions:]
    if len(set(recent_iterations)) == 1:  # All recent iterations are identical
        return True

    # Check for alternating pattern (A-B-A)
    return (
        len(fingerprints) >= 3
        and fingerprints[-1] == fingerprints[-3]
        and fingerprints[-1] != fingerprints[-2]
    )


def detect_fast_loop(state) -> bool:
    """Lightweight loop detection for fast mode - lower threshold."""
    iteration_entries = state.iterations
    min_actions = 2

    if len(iteration_entries) < min_actions:
        return False

    # Extract fingerprints from iteration entries
    fingerprints = [
        entry.get("fingerprint", "unknown")
        for entry in iteration_entries
        if entry and isinstance(entry, dict)
    ]

    # Check for excessive repetition (5+ identical)
    if len(fingerprints) >= 5:
        recent_iterations = fingerprints[-5:]
        if len(set(recent_iterations)) == 1:
            return True

    # Check for immediate back-and-forth (A-B-A) pattern
    return (
        len(fingerprints) >= 3
        and fingerprints[-1] == fingerprints[-3]
        and fingerprints[-1] != fingerprints[-2]
    )


def should_stop(state, react_mode: str) -> tuple[bool, str]:
    """Pure logic: check if reasoning should stop due to iteration limits or loops."""
    iteration = state.iteration
    max_iterations = state.max_iterations

    if iteration >= max_iterations:
        return True, "max_iterations_reached"

    # Adaptive loop detection based on mode
    if react_mode == "deep":
        loop_detected = detect_loop(state)
    else:
        loop_detected = detect_fast_loop(state)

    if loop_detected:
        return True, "reasoning_loop_detected"

    return False, ""
