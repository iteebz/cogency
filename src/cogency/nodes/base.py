"""Base node class for self-routing cognitive nodes."""

from functools import partial
from typing import Any

from resilient_result import unwrap

from cogency.state import State


class Node:
    """Self-routing cognitive node."""

    def __init__(self, func: Any, **kwargs):
        self.func = partial(func, **kwargs)

    async def __call__(self, state: State) -> State:
        result = await self.func(state)

        # Unwrap Result objects from @robust decorators
        if hasattr(result, "success"):
            try:
                return unwrap(result)
            except Exception as e:
                # Simple error propagation - add error to state and continue
                if isinstance(state, State):
                    state["error"] = str(e)
                    return state
                else:
                    # Fallback: create a new State with error
                    from cogency.context import Context

                    fallback_context = Context("error")
                    error_state = State(context=fallback_context, query="error")
                    error_state["error"] = str(e)
                    return error_state

        return result  # Already State

    def next_node(self, state: State) -> str:
        """Default: end flow."""
        return "respond"
