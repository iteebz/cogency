"""Base phase class for self-routing cognitive phases."""

from functools import partial
from typing import Any

from resilient_result import unwrap

from cogency.state import State


class Phase:
    """Self-routing cognitive phase."""

    def __init__(self, func: Any, **kwargs):
        self.func = partial(func, **kwargs)

    async def __call__(self, state: State, notifier=None) -> None:
        """Execute phase function - mutates state in place."""
        # All phase functions now require notifier parameter
        result = await self.func(state, notifier)

        # Handle Result objects from @robust decorators
        if hasattr(result, "success"):
            try:
                unwrap(result)  # Just unwrap, don't return - state already mutated
            except Exception as e:
                # Simple error propagation - add error to state
                state.error = str(e)

        # State was mutated in place by the function, no return needed

    def next_phase(self, state: State) -> str:
        """Default: end flow."""
        return "respond"
