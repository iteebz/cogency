"""Notification orchestration utilities."""

import asyncio
from typing import AsyncIterator, Optional


def format_thinking(thinking: Optional[str], mode: str = "fast") -> str:
    """Format thinking content for display."""
    if not thinking:
        return "Processing request..."

    # Add mode-specific emoji prefixes for visual distinction
    if mode == "deep":
        return f"🧠 {thinking}"
    else:
        return f"💭 {thinking}"


class Notifier:
    """Manages notifications for agent flows."""

    def __init__(self, state: State, phases: dict, trace: bool = False, verbose: bool = True):
        self.state = state
        self.phases = phases
        self.trace = trace
        self.verbose = verbose

    async def notify(self) -> AsyncIterator[str]:
        """Notify user of reasoning progress."""
        queue: asyncio.Queue[str] = asyncio.Queue()

        async def cb(message: str) -> None:
            await queue.put(message)

        # Set callback for notifications
        self.state.callback = cb
        self.state.notify = self.verbose
        self.state.debug = self.trace

        # Start execution in background
        from cogency.execution import run_agent

        task = asyncio.create_task(
            run_agent(
                self.state,
                self.phases["preprocess"],
                self.phases["reason"],
                self.phases["act"],
                self.phases["respond"],
            )
        )

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
