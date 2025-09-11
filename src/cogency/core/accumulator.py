"""Event accumulator: chunks flag controls streaming granularity."""

import json
import time
from collections.abc import AsyncGenerator, Callable
from typing import Any

from .executor import execute

# No more enum imports - just use strings


class Accumulator:
    """Event accumulator with streaming granularity control."""

    def __init__(
        self,
        config,
        user_id: str,
        conversation_id: str,
        chunks: bool = False,
        on_persist: Callable[[dict], None] | None = None,
    ):
        self.config = config
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.chunks = chunks
        self.on_persist = on_persist
        self.current_event_type = None
        self.accumulated_content = ""
        self.event_start_time = None
        self._pending_result = None

    async def process(
        self, parser_events: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process events: chunks=True streams immediately, chunks=False batches semantically."""

        async for event in parser_events:
            event_type = event["type"]
            content = event["content"]
            timestamp = event["timestamp"]

            if self.chunks:
                yield event

            state_changed = event_type != self.current_event_type

            if state_changed:
                # State change - yield previous accumulated event (chunks=False only)
                if not self.chunks and self.current_event_type and self.accumulated_content.strip():
                    yield {
                        "type": self.current_event_type,
                        "content": self.accumulated_content,
                        "timestamp": self.event_start_time,
                    }

                # Persist previous accumulated content
                if self.current_event_type and self.accumulated_content.strip():
                    await self._persist_accumulated_event()

                # Yield pending tool result if exists
                if self._pending_result:
                    yield self._pending_result
                    self._pending_result = None

                # Start new accumulation
                self.current_event_type = event_type
                self.accumulated_content = content
                self.event_start_time = timestamp
            else:
                # Same event type - accumulate content
                self.accumulated_content += content

        # Final flush - persist any remaining content
        if self.current_event_type and self.accumulated_content.strip():
            await self._persist_accumulated_event()

            # Yield final pending result if exists
            if self._pending_result:
                yield self._pending_result
                self._pending_result = None

            # Yield final event for non-chunks mode
            if not self.chunks:
                yield {
                    "type": self.current_event_type,
                    "content": self.accumulated_content,
                    "timestamp": self.event_start_time,
                }

    async def _persist_accumulated_event(self):
        """Persist complete accumulated event to DB."""
        if not self.on_persist:
            return

        complete_event = {
            "type": self.current_event_type,
            "content": self.accumulated_content.strip(),
            "timestamp": self.event_start_time or time.time(),
        }

        # Safe callback to persister
        self.on_persist(complete_event)

        # Tool execution on CALL event completion
        if self.current_event_type == "call":
            result_event = await self._execute_tool()
            # Store result event to yield after persistence
            self._pending_result = result_event

        # Reset accumulation
        self.accumulated_content = ""
        self.event_start_time = None

    async def _execute_tool(self):
        """Execute tool call and return result event."""
        try:
            # Parse tool call from accumulated content
            call_data = json.loads(self.accumulated_content.strip())

            # Execute single tool
            result = await execute(call_data, self.config, self.user_id, self.conversation_id)

            # Return result event for stream emission
            return {"type": "result", "content": result.outcome, "timestamp": time.time()}

        except (json.JSONDecodeError, Exception) as e:
            # Tool execution failed - return error result
            return {
                "type": "result",
                "content": f"Tool execution failed: {str(e)}",
                "timestamp": time.time(),
            }
