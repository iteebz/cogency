"""Base node class for self-routing cognitive nodes."""

from functools import partial
from typing import Any

from cogency.state import State


class Node:
    """Self-routing cognitive node."""
    
    def __init__(self, func: Any, **kwargs):
        self.func = partial(func, **kwargs)
    
    async def __call__(self, state: State) -> State:
        return await self.func(state)
    
    def next_node(self, state: State) -> str:
        """Default: end flow."""
        return "respond"