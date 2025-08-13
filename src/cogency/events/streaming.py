"""Event-coordinated streaming - real-time thinking + output via existing events."""

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass
class StreamEvent:
    """Streaming event with formatted content."""

    type: str  # "thinking", "response", "tool_use", "completion"
    content: str
    metadata: dict[str, Any] = None


class StreamingCoordinator:
    """Coordinates real-time streaming via existing event system - zero duplication."""

    def __init__(self, agent):
        self.agent = agent
        self._stream_queue = None
        self._stream_task = None
        self._event_handler = None

    async def stream_agent_run(
        self, query: str, user_id: str = "default"
    ) -> AsyncIterator[StreamEvent]:
        """Stream agent execution with real-time thinking and output."""
        # Create async queue for streaming events
        self._stream_queue = asyncio.Queue()

        # Create streaming event handler
        self._event_handler = StreamingEventHandler(self._stream_queue)

        # Subscribe to the agent's event bus
        from cogency.events.bus import _bus

        if _bus:
            _bus.subscribe(self._event_handler)

        # Start agent execution in background
        async def run_agent():
            try:
                result = await self.agent.run_async(query, user_id)
                # Signal completion with final result
                await self._stream_queue.put(
                    StreamEvent(type="completion", content=result, metadata={"final": True})
                )
            except Exception as e:
                await self._stream_queue.put(
                    StreamEvent(type="error", content=f"Error: {str(e)}", metadata={"error": True})
                )
            finally:
                # Signal end of stream
                await self._stream_queue.put(None)

        self._stream_task = asyncio.create_task(run_agent())

        # Yield events as they come
        while True:
            event = await self._stream_queue.get()
            if event is None:  # End of stream
                break
            yield event

        # Cleanup
        from cogency.events.bus import _bus as cleanup_bus

        if cleanup_bus and self._event_handler:
            cleanup_bus.handlers.remove(self._event_handler)

        # Ensure background task is complete
        await self._stream_task


class StreamingEventHandler:
    """Filters and formats existing events for streaming."""

    def __init__(self, stream_queue: asyncio.Queue):
        self.stream_queue = stream_queue
        self._last_thinking_time = 0
        self._recent_thinking = []

    def handle(self, event: dict):
        """Filter events and convert to streaming format."""
        event_type = event.get("type")
        data = event.get("data", {})

        # Convert events to streaming format
        if event_type == "reason":
            self._handle_reason_event(event, data)
        elif event_type == "tool":
            self._handle_tool_event(event, data)
        elif event_type == "agent":
            self._handle_agent_event(event, data)

    def _handle_reason_event(self, event: dict, data: dict):
        """Handle reasoning events - convert to thinking updates."""
        state = data.get("state")

        if state == "start":
            # Don't stream reasoning start - wait for actual thinking
            pass
        elif state == "llm_response":
            # This indicates LLM is generating a response - stream thinking placeholder
            iteration = data.get("iteration", 0)
            asyncio.create_task(
                self._queue_event(
                    StreamEvent(
                        type="thinking",
                        content=f"Analyzing request... (iteration {iteration})",
                        metadata={"iteration": iteration},
                    )
                )
            )
        elif state == "complete":
            response_type = data.get("type", "")
            if response_type == "direct_response":
                # Direct response path - will be handled by completion
                pass
            elif response_type == "actions_planned":
                actions_count = data.get("actions", 0)
                asyncio.create_task(
                    self._queue_event(
                        StreamEvent(
                            type="thinking",
                            content=f"Planning {actions_count} action(s)...",
                            metadata={"actions_planned": actions_count},
                        )
                    )
                )

    def _handle_tool_event(self, event: dict, data: dict):
        """Handle tool events - show tool usage."""
        operation = data.get("operation")
        name = data.get("name", "unknown")
        status = data.get("status")

        if status == "start":
            content = f"Using {name}..."
            if operation and operation != name:
                content = f"Using {name} ({operation})..."
        elif status == "complete":
            content = f"Completed {name}"
        elif status == "error":
            error = data.get("error", "unknown error")
            content = f"Error with {name}: {error}"
        else:
            return

        asyncio.create_task(
            self._queue_event(
                StreamEvent(
                    type="tool_use", content=content, metadata={"tool": name, "status": status}
                )
            )
        )

    def _handle_agent_event(self, event: dict, data: dict):
        """Handle agent-level events."""
        state = data.get("state")

        if state == "iteration":
            iteration = data.get("iteration", 0)
            if iteration > 0:  # Don't show iteration 0
                asyncio.create_task(
                    self._queue_event(
                        StreamEvent(
                            type="thinking",
                            content=f"Continue reasoning... (step {iteration + 1})",
                            metadata={"iteration": iteration},
                        )
                    )
                )
        elif state == "security_violation":
            error = data.get("error", "Security check failed")
            asyncio.create_task(
                self._queue_event(
                    StreamEvent(type="error", content=error, metadata={"security": True})
                )
            )

    async def _queue_event(self, stream_event: StreamEvent):
        """Queue event with rate limiting to avoid spam."""
        # Rate limit thinking events to avoid overwhelming output
        if stream_event.type == "thinking":
            current_time = time.time()
            if current_time - self._last_thinking_time < 0.5:  # 500ms cooldown
                return
            self._last_thinking_time = current_time

            # Avoid repetitive thinking
            if self._is_repetitive_thinking(stream_event.content):
                return

        await self.stream_queue.put(stream_event)

    def _is_repetitive_thinking(self, content: str) -> bool:
        """Avoid repetitive thinking content."""
        from cogency.events.thinking import is_repetitive_thinking

        is_repetitive = is_repetitive_thinking(content, self._recent_thinking)

        # Update recent thinking buffer
        self._recent_thinking.append(content)
        if len(self._recent_thinking) > 5:
            self._recent_thinking.pop(0)

        return is_repetitive


def format_stream_event(event: StreamEvent) -> str:
    """Format streaming event for console display."""
    from cogency.events.thinking import format_thinking

    if event.type == "thinking":
        return f"\r💭 {format_thinking(event.content)}"
    if event.type == "tool_use":
        status = event.metadata.get("status") if event.metadata else None
        if status == "start":
            return f"\r🔧 {event.content}"
        if status == "complete":
            return f"✅ {event.content}"
        if status == "error":
            return f"❌ {event.content}"
        return f"🔧 {event.content}"
    if event.type == "error":
        return f"\r❌ {event.content}"
    if event.type == "completion":
        return f"\r🎯 {event.content}"
    return f"\r{event.content}"
