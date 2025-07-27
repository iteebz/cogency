"""Notification orchestration utilities."""

import asyncio
from typing import AsyncIterator

from cogency.context import Context
from cogency.flow import Flow
from cogency.state import State


class Notifier:
    """Manages notifications for agent flows."""

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

    async def notify(self) -> AsyncIterator[str]:
        """Notify user of reasoning progress."""
        queue: asyncio.Queue[str] = asyncio.Queue()

        async def cb(message: str) -> None:
            await queue.put(message)

        # Create state for execution with notification parameters
        state = State(
            context=self.context,
            query=self.query,
            max_iterations=self.max_iterations,
            verbose=self.verbose,
            trace=self.trace,
            callback=cb,
        )

        # Start execution in background
        task = asyncio.create_task(self.flow.flow.ainvoke(state))

        # Notification messages as they arrive
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
            result = await task
            self._last_state = result  # Store final state for notification access

    def get_notifications(self) -> list:
        """Get the notification entries for debugging."""
        last_state = getattr(self, "_last_state", {})
        if isinstance(last_state, dict):
            return last_state.get("notifications", [])
        return []
