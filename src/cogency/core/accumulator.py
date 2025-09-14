"""Semantic event accumulator with streaming granularity control.

Transforms parser events into complete semantic units with persistence and tool execution.
The chunks flag controls streaming behavior: immediate vs batched emission.

Core responsibility: Accumulate fragmented events into coherent semantic blocks.
"""

import json
import time
from collections.abc import AsyncGenerator
from typing import Any

from ..lib.logger import logger
from ..lib.storage import save_message
from .executor import execute
from .protocols import ToolCall

# No more enum imports - just use strings


class Accumulator:
    """Semantic event accumulator with persistence and tool execution.

    Processes parser events into complete semantic units. Handles tool execution
    atomically with persistence. Controls streaming granularity via chunks flag.
    """

    def __init__(self, config, user_id: str, conversation_id: str, *, chunks: bool = False):
        self.config = config
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.chunks = chunks
        self.current_type = None
        self.content = ""
        self.start_time = None
        self._pending_result = None

    async def process(
        self, parser_events: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Transform parser events into complete semantic units.

        chunks=True: Stream events immediately (real-time)
        chunks=False: Batch events by semantic boundaries (coherent units)

        Handles tool execution and persistence atomically on state transitions.
        """

        async for event in parser_events:
            event_type = event["type"]
            content = event["content"]
            timestamp = time.time()  # Single timestamp when processing

            if self.chunks:
                yield event

            state_changed = event_type != self.current_type

            if state_changed:
                # State change - yield previous accumulated event (chunks=False only)
                if not self.chunks and self.current_type and self.content.strip():
                    yield {
                        "type": self.current_type,
                        "content": self.content,
                        "timestamp": self.start_time,
                    }

                # Persist previous accumulated content
                if self.current_type and self.content.strip():
                    await self._persist()

                # Yield pending tool result if exists
                if self._pending_result:
                    yield self._pending_result
                    self._pending_result = None

                # Start new accumulation
                self.current_type = event_type
                self.content = content
                self.start_time = timestamp
            else:
                # Same event type - accumulate content with spaces
                if (
                    self.content
                    and content
                    and not self.content.endswith(" ")
                    and not content.startswith(" ")
                ):
                    self.content += " "
                self.content += content

        # Final flush - persist any remaining content
        if self.current_type and self.content.strip():
            await self._persist()

            # Yield final pending result if exists
            if self._pending_result:
                yield self._pending_result
                self._pending_result = None

            # Yield final event for non-chunks mode
            if not self.chunks:
                yield {
                    "type": self.current_type,
                    "content": self.content,
                    "timestamp": self.start_time,
                }

    async def _persist(self):
        """Persist complete accumulated event to DB."""
        if not self.current_type or not self.content.strip():
            return

        # Direct persistence - no callback bullshit
        if self.current_type == "call":
            # Parse and store structured call data
            try:
                tool_call = ToolCall.from_json(self.content.strip())
                await save_message(
                    self.conversation_id,
                    self.user_id,
                    "call",
                    tool_call.to_json(),
                    timestamp=self.start_time,
                )
            except Exception as e:
                logger.warning(f"Failed to persist call data for conversation {self.conversation_id}: {e}")
                tool_call = ToolCall.from_json(self.content.strip())  # Still need to parse for execution

            # Execute tool after persistence (always happens)
            tool_event = await self._execute_tool(tool_call)
            self._pending_result = tool_event

            # Also save result message for conversation context
            try:
                await save_message(
                    self.conversation_id,
                    self.user_id,
                    "result",
                    tool_event["content"] or tool_event["outcome"],  # Full context or outcome
                )
            except Exception as e:
                logger.warning(f"Failed to persist result data for conversation {self.conversation_id}: {e}")

            except json.JSONDecodeError:
                # Invalid JSON - store as raw content
                try:
                    await save_message(
                        self.conversation_id,
                        self.user_id,
                        "call",
                        self.content.strip(),
                        timestamp=self.start_time,
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist invalid call data for conversation {self.conversation_id}: {e}")
        else:
            # Standard event types
            try:
                await save_message(
                    self.conversation_id,
                    self.user_id,
                    self.current_type,
                    self.content.strip(),
                    timestamp=self.start_time,
                )
            except Exception as e:
                logger.warning(f"Failed to persist {self.current_type} data for conversation {self.conversation_id}: {e}")

        # Reset accumulation
        self.content = ""
        self.start_time = None

    async def _execute_tool(self, tool_call: ToolCall):
        """Execute tool call and return tool event with clean formatting."""
        try:
            # Execute tool with structured call
            result = await execute(tool_call, self.config, self.user_id, self.conversation_id)

            return {
                "type": "result",
                "outcome": result.outcome,
                "content": result.content,
            }

        except Exception as e:
            # Tool execution failed - return error event
            return {
                "type": "result",
                "outcome": f"Error: {str(e)}",
                "content": f"Tool execution failed: {str(e)}",
            }
