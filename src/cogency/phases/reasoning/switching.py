"""Mode switching criteria and logic for adaptive reasoning"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_switch(llm_response: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract mode switching directives from LLM JSON response"""
    try:
        from cogency.utils import parse_json

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
    """Switch reasoning mode - only changes mode, keeps all context"""
    # Update react mode
    state["mode"] = new_mode

    # Track mode switch if state is a State object
    if hasattr(state, "switch_mode"):
        state.switch_mode(new_mode, switch_why)

    return state
