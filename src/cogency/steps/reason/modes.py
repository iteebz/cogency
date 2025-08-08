"""Mode switching controller - centralized decision logic."""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ModeController:
    """Centralized mode switching decisions and guidelines."""

    @staticmethod
    def should_switch(
        current_mode: str,
        requested_mode: Optional[str],
        reason: Optional[str],
        iteration: int,
        max_iterations: int,
    ) -> bool:
        """Single source of truth for mode switching decisions."""
        if not requested_mode or not reason:
            return False

        # Must be different from current mode
        if requested_mode == current_mode:
            return False

        # Only allow valid modes
        if requested_mode not in ["fast", "deep", "adapt"]:
            return False

        # Prevent switching too early (let mode try at least once)
        if iteration < 1:
            return False

        # FORCE downshift near max iterations
        if current_mode == "deep" and requested_mode == "fast" and iteration >= max_iterations - 2:
            logger.info(
                f"Forced de-escalation: deep→fast at iteration {iteration}/{max_iterations}"
            )
            return True

        # Allow downshift if deep mode stalled
        if (
            current_mode == "deep"
            and requested_mode == "fast"
            and iteration >= 2
            and "no progress" in reason.lower()
        ):
            logger.info(f"Stall de-escalation: deep mode at iteration {iteration}")
            return True

        # STRICT downshift validation for deep→fast
        if current_mode == "deep" and requested_mode == "fast":
            valid_reasons = [
                "analysis complete",
                "synthesis complete",
                "simple execution remains",
                "single tool sufficient",
                "max_iterations",
                "direct action",
            ]

            if not any(valid_reason in reason.lower() for valid_reason in valid_reasons):
                logger.info(f"Blocked premature deep→fast: '{reason}'")
                return False

        # Prevent switching too late - but allow final iteration switches for completion
        return iteration <= max_iterations

    @staticmethod
    def get_switch_guidelines(current_mode: str, max_iterations: int) -> str:
        """Generate mode switching guidelines from decision logic."""
        if current_mode == "deep":
            return f"""DOWNSHIFT to FAST if:
- Analysis complete, simple execution remains
- Synthesis complete, only direct action needed
- Single tool sufficient for remaining work
- Approaching max_iterations limit ({max_iterations} iterations)
- Deep mode not making progress

NEVER DOWNSHIFT if:
- Multi-step reasoning in progress
- Conflicting information needs synthesis
- Complex analysis still required

Examples:
switch_to: "fast", switch_why: "Analysis complete, simple execution remains"
switch_to: "fast", switch_why: "Approaching max_iterations limit, need direct action\""""

        elif current_mode == "fast":
            return """ESCALATE to DEEP if:
- Tool results conflict and need synthesis
- Multi-step reasoning chains required
- Ambiguous requirements need breakdown
- Complex analysis beyond direct execution

Examples:
switch_to: "deep", switch_why: "Search results contradict, need analysis"
switch_to: "deep", switch_why: "Multi-step reasoning required\""""

        else:  # adapt mode
            return """ADAPT MODE: Dynamic reasoning
- ESCALATE to deep when complexity emerges
- DOWNSHIFT to fast when analysis complete
- Choose mode based on task requirements

ESCALATE to DEEP: Tool conflicts, multi-step reasoning, complex analysis
DOWNSHIFT to FAST: Analysis complete, simple execution remains"""

    @staticmethod
    def parse_switch_request(raw_response: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract mode switching directives from LLM response."""
        from cogency.utils.parsing import _parse_json

        try:
            result = _parse_json(raw_response)
            if result.success:
                data = result.data

                # Handle list responses - extract first dict
                if isinstance(data, list):
                    data = data[0] if data and isinstance(data[0], dict) else {}

                # Extract switch fields
                if isinstance(data, dict):
                    return data.get("switch_to"), data.get("switch_why")
                else:
                    logger.warning(f"Switch parse: unexpected data type {type(data)}")
            else:
                logger.warning("Switch parse: JSON parsing failed")
        except Exception as e:
            logger.error(f"Switch parse error: {e}")

        return None, None

    @staticmethod
    def execute_switch(state, new_mode: str, reason: str) -> None:
        """Execute mode switch - minimal state update."""
        from cogency.state.mutations import autosave

        state.mode = new_mode
        autosave(state)
