"""Mode switching criteria and logic for adaptive reasoning"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_switch(llm_response: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract mode switching directives from LLM JSON response"""
    try:
        from cogency.utils.parsing import parse_json

        result = parse_json(llm_response)
        if result.success:
            data = result.data
            return data.get("switch_to"), data.get("switch_why")
    except Exception as e:
        logger.error(f"Context: {e}")
        pass

    return None, None


def should_switch(
    current_mode: str,
    switch_to: Optional[str],
    switch_why: Optional[str],
    iteration: int = 0,
) -> bool:
    """Determine if mode switch should occur based on request and iteration context"""
    if not switch_to or not switch_why:
        return False

    # Must be different from current mode
    if switch_to == current_mode:
        return False

    # Only allow valid mode transitions
    if switch_to not in ["fast", "deep"]:
        return False

    # Prevent switching too early (let mode try at least once)
    if iteration < 1:
        return False

    # Prevent switching too late (close to max iterations)
    return not iteration >= 4


def switch_mode(state: Dict[str, Any], new_mode: str, switch_why: str) -> Dict[str, Any]:
    """Switch reasoning mode while preserving cognitive context and tracking history"""
    # Capture old mode before any changes
    old_mode = state.get("react_mode", "unknown")

    # Update react mode
    state["react_mode"] = new_mode

    # Preserve cognitive state but update mode-specific limits
    if "cognition" in state:
        cognition = state["cognition"]
        cognition.react_mode = new_mode

        # CRITICAL FIX: Preserve context before changing limits
        old_max_history = getattr(cognition, "max_history", 10)

        # Adjust memory limits for new mode
        if new_mode == "fast":
            new_max_history = 3
            cognition.max_failures = 5
        else:  # deep
            new_max_history = 10
            cognition.max_failures = 15

        # If switching to more restrictive mode, preserve context first
        if new_max_history < old_max_history and len(cognition.iterations) > new_max_history:
            # Extract cognitive summary from iterations that will be truncated
            iterations_to_preserve = cognition.iterations[:-new_max_history]
            if iterations_to_preserve and not cognition.preserved_context:
                cognition.preserved_context = cognition._extract_cognitive_summary(
                    iterations_to_preserve
                )

        # Now safe to change max_history - truncation with preservation handled in update()
        cognition.max_history = new_max_history

    # Track mode switch for tracing
    if "cognition" in state:
        state["cognition"].switch_mode(new_mode, switch_why)

    # Maintain legacy mode tracking for backward compatibility
    mode_switches = state.get("mode_switches", [])
    mode_switches.append(
        {
            "from_mode": old_mode,
            "to_mode": new_mode,
            "reason": switch_why,
            "iteration": state.get("iteration", 0),
        }
    )
    state["mode_switches"] = mode_switches
    state["previous_react_mode"] = old_mode

    return state


def switch_prompt(current_mode: str) -> str:
    """Get mode-specific prompt addition for bidirectional cognitive switching"""
    if current_mode == "deep":
        return """
COGNITIVE ADJUSTMENT: If this task is simpler than expected, you can downshift to fast mode.

Output JSON with mode switching:
{
  "reasoning": "your analysis",
  "strategy": "approach_name",
  "switch_to": "fast" | null,
  "switch_reason": "why switching modes" | null
}"""
    else:  # fast
        return """
COGNITIVE ADJUSTMENT: If this needs deeper analysis, complex synthesis, or multi-step reasoning, escalate to deep mode.

Output JSON with escalation:
{
  "reasoning": "brief thought",
  "strategy": "direct_approach",
  "switch_to": "deep" | null,
  "switch_reason": "why switching modes" | null
}"""
