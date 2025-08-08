"""Core reasoning functions - consolidated business logic."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from cogency.state import State
from cogency.tools import Tool
from cogency.utils.parsing import _parse_json

logger = logging.getLogger(__name__)


def build_reasoning_prompt(
    state: State, tools: List[Tool], memory=None, identity: str = None
) -> str:
    """Build reasoning prompt from current context."""
    from .prompt import Prompt

    prompt_builder = Prompt()
    return prompt_builder.build(state, tools, identity=identity)


def build_messages(prompt: str, state: State) -> List[Dict[str, str]]:
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


async def _switch_mode(state: State, raw_response: str, mode: str, iteration: int) -> None:
    """Handle complete mode switching logic."""
    from .modes import ModeController

    # Handle mode switching - only if agent mode is "adapt"
    agent_mode = getattr(state, "agent_mode", "adapt")
    if agent_mode != "adapt":
        return

    # Parse switch request from LLM response
    switch_to, switch_why = ModeController.parse_switch_request(raw_response)

    # Check if switch should be executed
    if ModeController.should_switch(
        mode, switch_to, switch_why, iteration, state.execution.max_iterations
    ):
        # Execute the mode switch
        ModeController.execute_switch(state, switch_to, switch_why)
