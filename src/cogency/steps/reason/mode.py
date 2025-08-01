"""Mode switching for reasoning - LLM-driven adaptive mode switching."""

import logging
from typing import Optional, Tuple

from cogency.state import State

logger = logging.getLogger(__name__)


class Mode:
    """Handles LLM-driven adaptive mode switching."""

    def parse(self, raw_response: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract mode switching directives from LLM JSON response."""
        try:
            from cogency.utils import parse_json

            result = parse_json(raw_response)
            if result.success:
                data = result.data
                return data.get("switch_to"), data.get("switch_why")
        except Exception as e:
            logger.error(f"Context: {e}")
            pass

        return None, None

    def should_switch(
        self,
        current_mode: str,
        switch_to: Optional[str],
        switch_why: Optional[str],
        iteration: int = 0,
        depth: int = 5,
    ) -> bool:
        """Determine if mode switch should occur based on request and iteration context."""
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

        # DE-ESCALATION: Force switch from deep to fast if approaching depth limit
        if current_mode == "deep" and switch_to == "fast" and iteration >= depth - 2:
            logger.info(f"De-escalation: forcing deep→fast at iteration {iteration}/{depth}")
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
        return not iteration >= depth - 1

    def switch(self, state: State, new_mode: str, switch_why: str) -> None:
        """Switch reasoning mode - only changes mode, keeps all context."""
        # Update react mode
        state.mode = new_mode

        # Track mode switch if state has the method
        if hasattr(state, "switch_mode"):
            state.switch_mode(new_mode, switch_why)

    async def handle_switch(
        self, state: State, raw_response: str, mode: str, iteration: int, notifier
    ) -> None:
        """Handle complete mode switching logic - preserves LLM-driven adaptation."""
        # Handle mode switching - only if agent mode is "adapt"
        agent_mode = getattr(state, "agent_mode", "adapt")
        if agent_mode != "adapt":
            return

        # Parse switch request from LLM response
        switch_to, switch_why = self.parse(raw_response)

        # Check if switch should be executed
        if self.should_switch(mode, switch_to, switch_why, iteration, state.depth):
            await notifier(
                "trace",
                message="Mode switch executed",
                from_mode=mode,
                to_mode=switch_to,
                reason=switch_why,
                iteration=iteration,
            )

            # Execute the mode switch
            self.switch(state, switch_to, switch_why)
