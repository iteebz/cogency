"""Base phase class for self-routing cognitive phases."""

from functools import partial
from typing import Any, Optional

from resilient_result import unwrap

from cogency.state import State


class Phase:
    """Self-routing cognitive phase."""

    def __init__(self, func: Any, **kwargs):
        self.func = partial(func, **kwargs)

    async def __call__(self, state: State, notifier=None) -> Optional[str]:
        """Execute phase function - may return early response or None."""
        # All phase functions now require notifier parameter
        result = await self.func(state, notifier)

        # Handle Result objects from @robust decorators
        if hasattr(result, "success"):
            try:
                result = unwrap(result)
            except Exception as e:
                # Fail fast with structured error context
                raise RuntimeError(f"Phase {self.func.func.__name__} failed: {str(e)}") from e

        # Return the result if it's a string (early response)
        if isinstance(result, str):
            return result

        return None
