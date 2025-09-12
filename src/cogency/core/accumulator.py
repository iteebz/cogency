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
from .executor import execute

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
            timestamp = event["timestamp"]

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

        from ..lib.storage import save_message

        # Direct persistence - no callback bullshit
        if self.current_type == "call":
            # Parse and store structured call data
            try:
                call_data = json.loads(self.content.strip())
                save_success = await save_message(
                    self.conversation_id,
                    self.user_id,
                    "call",
                    json.dumps(call_data),
                    timestamp=self.start_time,
                )
                if not save_success:
                    logger.warning(
                        f"Failed to persist call data for conversation {self.conversation_id}"
                    )

                # Execute tool after persistence
                tool_event = await self._execute_tool()
                self._pending_result = tool_event
                
                # Also save result message for conversation context
                await save_message(
                    self.conversation_id,
                    self.user_id,
                    "result", 
                    tool_event["result_agent"],  # Agent gets full result
                    timestamp=tool_event["timestamp"],
                )

            except json.JSONDecodeError:
                # Invalid JSON - store as raw content
                save_success = await save_message(
                    self.conversation_id,
                    self.user_id,
                    "call",
                    self.content.strip(),
                    timestamp=self.start_time,
                )
                if not save_success:
                    logger.warning(
                        f"Failed to persist invalid call data for conversation {self.conversation_id}"
                    )
        else:
            # Standard event types
            save_success = await save_message(
                self.conversation_id,
                self.user_id,
                self.current_type,
                self.content.strip(),
                timestamp=self.start_time,
            )
            if not save_success:
                logger.warning(
                    f"Failed to persist {self.current_type} data for conversation {self.conversation_id}"
                )

        # Reset accumulation
        self.content = ""
        self.start_time = None

    async def _execute_tool(self):
        """Execute tool call and return tool event with human/agent formatting."""
        try:
            # Parse tool call from accumulated content
            call_data = json.loads(self.content.strip())
            
            # Get tool for describe_action
            from cogency.tools import TOOLS
            tool_name = call_data.get("name", "unknown")
            tool = next((t for t in TOOLS if t.name == tool_name), None)
            
            # Execute single tool
            result = await execute(call_data, self.config, self.user_id, self.conversation_id)
            
            # Create tool event with human/agent formatting
            action_display = tool.describe_action(**call_data.get("args", {})) if tool else f"Running {tool_name}"
            
            return {
                "type": "tool",
                "display": action_display,  # Human display: "Creating config.py"
                "status": "success",
                "result_human": result.for_human(),  # Human result: outcome only
                "result_agent": result.for_agent(),  # Agent result: outcome + content
                "timestamp": time.time(),
            }

        except (json.JSONDecodeError, Exception) as e:
            # Tool execution failed - return error tool event
            return {
                "type": "tool", 
                "display": "Tool execution failed",
                "status": "error",
                "result_human": f"Error: {str(e)}",
                "result_agent": f"Tool execution failed: {str(e)}",
                "timestamp": time.time(),
            }
