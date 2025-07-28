"""Notification orchestration utilities."""

import asyncio
from typing import AsyncIterator, Optional

from cogency.state import State


async def notify(state: State, event_type: str, message: str) -> None:
    """Clean notification function - no coupling to state methods."""
    if state.callback and state.verbose and callable(state.callback):
        import asyncio
        if asyncio.iscoroutinefunction(state.callback):
            await state.callback(f"{event_type}: {message}")
        else:
            state.callback(f"{event_type}: {message}")


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

    def __init__(
        self,
        state: State,
        llm,
        tools,
        memory,
        system_prompt: str,
        identity: str,
        json_schema,
        trace: bool = False,
        verbose: bool = True,
    ):
        self.state = state
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.system_prompt = system_prompt
        self.identity = identity
        self.json_schema = json_schema
        self.trace = trace
        self.verbose = verbose

    async def notify(self) -> AsyncIterator[str]:
        """Notify user of reasoning progress."""
        queue: asyncio.Queue[str] = asyncio.Queue()

        async def cb(message: str) -> None:
            await queue.put(message)

        # Set callback for notifications
        self.state.callback = cb
        self.state.verbose = self.verbose
        self.state.trace = self.trace

        # Start execution in background
        from cogency.execution import run_agent
        kwargs = {
            "llm": self.llm,
            "tools": self.tools,
            "memory": self.memory,
            "system_prompt": self.system_prompt,
            "identity": self.identity,
            "json_schema": self.json_schema,
        }
        task = asyncio.create_task(run_agent(self.state, **kwargs))

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
