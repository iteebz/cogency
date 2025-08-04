"""Core reasoning functions - consolidated business logic."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from cogency.events import emit
from cogency.state import AgentState
from cogency.tools import Tool
from cogency.utils.parsing import _parse_json

logger = logging.getLogger(__name__)


def build_reasoning_prompt(state: AgentState, tools: List[Tool], memory=None) -> str:
    """Build reasoning prompt from current context."""
    from cogency.state.context import reasoning_context

    mode = state.execution.mode
    return reasoning_context(state, tools, mode)


def build_messages(prompt: str, state: AgentState) -> List[Dict[str, str]]:
    """Build message array for LLM."""
    messages = [{"role": "system", "content": prompt}]
    messages.extend(
        [{"role": msg["role"], "content": msg["content"]} for msg in state.execution.messages]
    )
    return messages


def parse_reasoning_response(raw_response: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Parse LLM response into structured data."""
    parsed = _parse_json(raw_response)
    return parsed.success, parsed.data if parsed.success else None


def should_mode_switch(
    current_mode: str,
    switch_to: Optional[str],
    switch_why: Optional[str],
    iteration: int,
    max_iterations: int,
) -> bool:
    """Determine if mode switch should occur."""
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

    # DE-ESCALATION: Force switch from deep to fast if approaching max_iterations limit
    if current_mode == "deep" and switch_to == "fast" and iteration >= max_iterations - 2:
        logger.info(f"De-escalation: forcing deep→fast at iteration {iteration}/{max_iterations}")
        return True

    # DE-ESCALATION: Switch to fast if deep mode isn't making progress
    if (
        current_mode == "deep"
        and switch_to == "fast"
        and iteration >= 2
        and "no progress" in switch_why.lower()
    ):
        logger.info(f"De-escalation: deep mode stalled at iteration {iteration}")
        return True

    # Prevent switching too late (close to max iterations)
    return not iteration >= max_iterations - 1


def parse_mode_switch(raw_response: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract mode switching directives from LLM JSON response."""
    try:
        result = _parse_json(raw_response)
        if result.success:
            data = result.data
            return data.get("switch_to"), data.get("switch_why")
    except Exception as e:
        logger.error(f"Mode switch parse error: {e}")

    return None, None


def execute_mode_switch(state: AgentState, new_mode: str, switch_why: str) -> None:
    """Switch reasoning mode - only changes mode, keeps all context."""
    state.execution.mode = new_mode

    # Track mode switch if state has the method
    if hasattr(state, "switch_mode"):
        state.switch_mode(new_mode, switch_why)


async def _switch_mode(state: AgentState, raw_response: str, mode: str, iteration: int) -> None:
    """Handle complete mode switching logic."""
    # Handle mode switching - only if agent mode is "adapt"
    agent_mode = getattr(state, "agent_mode", "adapt")
    if agent_mode != "adapt":
        return

    # Parse switch request from LLM response
    switch_to, switch_why = parse_mode_switch(raw_response)

    # Check if switch should be executed
    if should_mode_switch(mode, switch_to, switch_why, iteration, state.execution.max_iterations):
        emit(
            "trace",
            message="Mode switch executed",
            from_mode=mode,
            to_mode=switch_to,
            reason=switch_why,
            iteration=iteration,
        )

        # Execute the mode switch
        execute_mode_switch(state, switch_to, switch_why)
