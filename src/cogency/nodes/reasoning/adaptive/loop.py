"""Action loop detection and prevention."""

from typing import Any, List

LOOP_DETECTION_MIN_ACTIONS = 3
FAST_LOOP_DETECTION_MIN_ACTIONS = 2
SEARCH_FINGERPRINT_KEY_TERMS = 5


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
            key_args = {
                k: v
                for k, v in args.items()
                if k
                in [
                    "query",
                    "url",
                    "code",
                    "content",
                    "operation",
                    "command",
                    "filename",
                    "action",
                ]
            }
            # For search queries, normalize to catch similar searches
            if tool_name == "search" and "query" in key_args:
                query = key_args["query"].lower()
                # Extract key terms to catch semantic similarity
                key_terms = set(
                    query.split()[:SEARCH_FINGERPRINT_KEY_TERMS]
                )  # First 5 words as key terms
                fingerprint = f"{tool_name}:{hash(str(sorted(key_terms)))}"
            else:
                fingerprint = f"{tool_name}:{hash(str(sorted(key_args.items())))}"
        else:
            fingerprint = f"{tool_name}:{hash(str(args))}"

        fingerprints.append(fingerprint)

    return "|".join(fingerprints)


def detect_loop(cognition) -> bool:
    """Detect if agent is stuck in an iteration loop."""
    iteration_entries = cognition.iterations

    if len(iteration_entries) < LOOP_DETECTION_MIN_ACTIONS:
        return False

    # Extract fingerprints from iteration entries
    fingerprints = [
        entry.get("fingerprint", "unknown")
        for entry in iteration_entries
        if entry and isinstance(entry, dict)
    ]

    # Check for repeated identical iterations
    recent_iterations = fingerprints[-LOOP_DETECTION_MIN_ACTIONS:]
    if len(set(recent_iterations)) == 1:  # All 3 recent iterations are identical
        return True

    # Check for alternating pattern (A-B-A)
    return (
        len(fingerprints) >= 3
        and fingerprints[-1] == fingerprints[-3]
        and fingerprints[-1] != fingerprints[-2]
    )


def detect_fast_loop(cognition) -> bool:
    """Lightweight loop detection for fast mode - lower threshold."""
    iteration_entries = cognition.iterations

    # Fast mode: detect loops earlier - even just 2 identical iterations
    if len(iteration_entries) < FAST_LOOP_DETECTION_MIN_ACTIONS:
        return False

    # Extract fingerprints from iteration entries
    fingerprints = [
        entry.get("fingerprint", "unknown")
        for entry in iteration_entries
        if entry and isinstance(entry, dict)
    ]

    # Check for excessive repetition (5+ identical) - verification up to 4x is reasonable
    if len(fingerprints) >= 5:
        recent_iterations = fingerprints[-5:]
        if len(set(recent_iterations)) == 1:  # All 5 identical
            return True

    # Check for immediate back-and-forth (A-B-A) pattern
    return (
        len(fingerprints) >= LOOP_DETECTION_MIN_ACTIONS
        and fingerprints[-1] == fingerprints[-LOOP_DETECTION_MIN_ACTIONS]
        and fingerprints[-1] != fingerprints[-2]
    )


def should_stop_reasoning(state, react_mode: str) -> tuple[bool, str]:
    """Pure logic: check if reasoning should stop due to iteration limits or loops."""
    iteration = state.iteration
    max_iterations = state.max_iterations

    if iteration >= max_iterations:
        return True, "max_iterations_reached"

    # Adaptive loop detection based on mode
    if react_mode == "deep":
        loop_detected = detect_loop(state.cognition)
    else:
        loop_detected = detect_fast_loop(state.cognition)

    if loop_detected:
        return True, "reasoning_loop_detected"

    return False, ""
