"""Mode switching criteria and logic for adaptive reasoning"""

import json
from typing import Any, Dict, Optional, Tuple


def switching_criteria(current_mode: str) -> str:
    """Get detailed mode switching criteria for prompts."""
    if current_mode == "fast":
        return """
ESCALATE to DEEP MODE if task requires:
- Complex analysis or synthesis
- Multi-step reasoning chains
- Breaking down complex problems
- Comparing multiple approaches
- Handling ambiguous requirements

JSON: {{"thinking": "brief analysis", "decision": "approach", "switch_to": "deep"|null, "switch_why": "escalation reason"|null}}"""
    else:  # deep mode
        return """
DOWNSHIFT to FAST MODE if task is:
- Simple direct action
- Single-step execution
- Clear straightforward request
- No complex analysis needed

JSON: {{"thinking": {{"reflection": "...", "planning": "...", "decision": "..."}}, "switch_to": "fast"|null, "switch_why": "downshift reason"|null}}"""


def parse_switch(llm_response: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract mode switching directives from LLM JSON response"""
    try:
        # Try to extract JSON from response
        start = llm_response.find("{")
        end = llm_response.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = llm_response[start:end]
            data = json.loads(json_str)

            # Handle both escalate_to (old) and switch_to (new) formats
            switch_to = data.get("switch_to") or data.get("escalate_to")
            switch_reason = data.get("switch_reason") or data.get("escalation_reason")

            return switch_to, switch_reason
    except (json.JSONDecodeError, ValueError):
        pass

    return None, None


def should_switch(
    current_mode: str,
    switch_to: Optional[str],
    switch_reason: Optional[str],
    current_iteration: int = 0,
) -> bool:
    """Determine if mode switch should occur based on request and iteration context"""
    if not switch_to or not switch_reason:
        return False

    # Must be different from current mode
    if switch_to == current_mode:
        return False

    # Only allow valid mode transitions
    if switch_to not in ["fast", "deep"]:
        return False

    # Prevent switching too early (let mode try at least once)
    if current_iteration < 1:
        return False

    # Prevent switching too late (close to max iterations)
    return not current_iteration >= 4


def switch_mode(state: Dict[str, Any], new_mode: str, switch_reason: str) -> Dict[str, Any]:
    """Switch reasoning mode while preserving cognitive context and tracking history"""
    # Update react mode
    state["react_mode"] = new_mode

    # Preserve cognitive state but update mode-specific limits
    if "cognition" in state:
        cognition = state["cognition"]
        cognition["react_mode"] = new_mode

        # Adjust memory limits for new mode
        if new_mode == "fast":
            cognition["max_history"] = 3
            cognition["max_failures"] = 5
        else:  # deep
            cognition["max_history"] = 10
            cognition["max_failures"] = 15

    # Track mode switch for tracing
    mode_switches = state.get("mode_switches", [])
    mode_switches.append(
        {
            "from_mode": state.get("previous_react_mode", "unknown"),
            "to_mode": new_mode,
            "reason": switch_reason,
            "iteration": state.get("current_iteration", 0),
        }
    )
    state["mode_switches"] = mode_switches
    state["previous_react_mode"] = state.get("react_mode", "unknown")

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
