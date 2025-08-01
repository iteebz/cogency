"""Response parsing for reasoning - JSON parsing and validation."""

from typing import Optional

from cogency.steps.reason.types import Reasoning
from cogency.utils import parse_json


class Parse:
    """Parses LLM reasoning responses into structured objects."""

    async def reasoning(
        self, raw_response: str, notifier, mode: str, iteration: int
    ) -> Optional[Reasoning]:
        """Parse raw LLM response into Reasoning object."""
        # Parse JSON response - fail fast with Result pattern
        parse_result = parse_json(raw_response)

        # Let Result pattern propagate naturally - no silent fallback
        reasoning_response = (
            Reasoning.from_dict(parse_result.data) if parse_result.success else None
        )

        # Trace parsing failures for debugging
        if not parse_result.success:
            await notifier(
                "trace",
                message="LLM response parse failed",
                mode=mode,
                iteration=iteration,
                error="invalid_reasoning_format",
            )

        return reasoning_response

    async def mode(self, raw_response: str):
        """Parse mode switching from LLM response."""
        from .switching import parse_switch

        return parse_switch(raw_response)
