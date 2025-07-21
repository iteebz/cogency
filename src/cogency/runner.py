"""Clean flow execution."""

from typing import Awaitable, Callable

from cogency.state import State


class StreamRunner:
    """Flow execution with streaming support."""

    async def stream(self, flow, state: State, stream_cb: Callable[[str], Awaitable[None]]):
        """Execute flow with streaming callback for user updates."""
        if stream_cb:
            state.output.callback = stream_cb

        return await flow.ainvoke(state)
