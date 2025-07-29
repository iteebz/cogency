"""Notification orchestration utilities."""

import asyncio
from typing import AsyncIterator, Optional

from cogency.state import State


async def notify(state: State, event_type: str, message: str) -> None:
    """Clean notification function - separate verbose and trace channels."""
    notification_entry = {
        "event_type": event_type,
        "data": message,
        "iteration": state.iteration,
    }
    state.notifications.append(notification_entry)

    if not state.callback or not callable(state.callback):
        return

    # Canonical phase notifications (verbose=True)
    phase_events = {"preprocess", "reason", "act", "respond"}
    
    # Send phase notifications if notify enabled
    if event_type in phase_events and state.notify:
        if asyncio.iscoroutinefunction(state.callback):
            await state.callback(f"{event_type}: {message}")
        else:
            state.callback(f"{event_type}: {message}")
    
    # Send debug notifications if debug enabled
    elif event_type == "trace" and state.debug:
        if asyncio.iscoroutinefunction(state.callback):
            await state.callback(f"TRACE: {message}")
        else:
            state.callback(f"TRACE: {message}")


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
        self.state.notify = self.verbose
        self.state.debug = self.trace

        # Start execution in background
        from cogency.execution import run_agent
        from cogency.phases.preprocess import Preprocess
        from cogency.phases.reason import Reason
        from cogency.phases.act import Act
        from cogency.phases.respond import Respond
        
        # Create phase instances with dependencies
        preprocess_phase = Preprocess(self.llm, self.tools, self.memory, self.system_prompt, self.identity)
        reason_phase = Reason(self.llm, self.tools, self.system_prompt, self.identity)
        act_phase = Act(self.llm, self.tools, self.system_prompt, self.identity)
        respond_phase = Respond(self.llm, self.tools, self.system_prompt, self.identity, self.json_schema)
        
        task = asyncio.create_task(run_agent(self.state, preprocess_phase, reason_phase, act_phase, respond_phase))

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
