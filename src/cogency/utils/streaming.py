"""Stream orchestration utilities."""

import asyncio
from typing import AsyncIterator

from cogency.context import Context
from cogency.flow import Flow
from cogency.output import Output
from cogency.state import State


class StreamManager:
    """Manages streaming execution of agent flows."""

    def __init__(
        self,
        flow: Flow,
        context: Context,
        query: str,
        trace: bool = False,
        verbose: bool = True,
        max_iterations: int = 10,
    ):
        self.flow = flow
        self.context = context
        self.query = query
        self.trace = trace
        self.verbose = verbose
        self.max_iterations = max_iterations

    async def stream(self) -> AsyncIterator[str]:
        """Stream flow execution with real-time message delivery."""
        queue: asyncio.Queue[str] = asyncio.Queue()

        async def cb(message: str) -> None:
            await queue.put(message)

        # Create output manager with callback
        output = Output(trace=self.trace, verbose=self.verbose, callback=cb)
        self._last_output = output  # Store for traces access

        # Create state for execution
        state = State(context=self.context, query=self.query, output=output)
        state["MAX_ITERATIONS"] = self.max_iterations
        state["verbose"] = self.verbose

        # Start execution in background
        task = asyncio.create_task(self.flow.flow.ainvoke(state))

        # Stream messages as they arrive
        try:
            while not task.done():
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield message
                except asyncio.TimeoutError:
                    continue

            # Get any remaining messages
            while not queue.empty():
                yield queue.get_nowait()

        finally:
            await task

    def get_output(self) -> Output:
        """Get the output manager for traces access."""
        return self._last_output if hasattr(self, "_last_output") else None
