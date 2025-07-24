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
    """Detect if agent is stuck in an action loop."""
    action_entries = cognition.action_fingerprints

    if len(action_entries) < LOOP_DETECTION_MIN_ACTIONS:
        return False

    # Extract fingerprints from dict entries
    fingerprints = [entry["fingerprint"] for entry in action_entries]

    # Check for repeated identical actions
    recent_actions = fingerprints[-LOOP_DETECTION_MIN_ACTIONS:]
    if len(set(recent_actions)) == 1:  # All 3 recent actions are identical
        return True

    # Check for alternating pattern (A-B-A)
    return (
        len(fingerprints) >= 3
        and fingerprints[-1] == fingerprints[-3]
        and fingerprints[-1] != fingerprints[-2]
    )


def detect_fast_loop(cognition) -> bool:
    """Lightweight loop detection for fast mode - lower threshold."""
    action_entries = cognition.action_fingerprints

    # Fast mode: detect loops earlier - even just 2 identical actions
    if len(action_entries) < FAST_LOOP_DETECTION_MIN_ACTIONS:
        return False

    # Extract fingerprints from dict entries
    fingerprints = [entry["fingerprint"] for entry in action_entries]

    # Check for immediate repetition (A-A) - fast detection
    if (
        len(fingerprints) >= FAST_LOOP_DETECTION_MIN_ACTIONS
        and fingerprints[-1] == fingerprints[-2]
    ):
        return True

    # Check for exact repetition pattern (A-A-A) - truly identical actions
    if len(fingerprints) >= LOOP_DETECTION_MIN_ACTIONS:
        recent_actions = fingerprints[-LOOP_DETECTION_MIN_ACTIONS:]
        if len(set(recent_actions)) == 1:  # All 3 identical
            return True

    # Check for immediate back-and-forth (A-B-A) pattern
    return (
        len(fingerprints) >= LOOP_DETECTION_MIN_ACTIONS
        and fingerprints[-1] == fingerprints[-LOOP_DETECTION_MIN_ACTIONS]
        and fingerprints[-1] != fingerprints[-2]
    )
