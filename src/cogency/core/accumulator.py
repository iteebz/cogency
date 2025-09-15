"""Event accumulator with tool execution and persistence.

Core algorithm:
1. Accumulate content until type changes or control events (§execute, §end)
2. Execute tool calls when §execute encountered
3. Persist all events via specialized EventPersister
4. Streaming modes:
   - chunks=True: Yield individual events immediately AND accumulate for tools
   - chunks=False: Only accumulate, yield complete semantic units on type changes
   Both modes accumulate for tool execution (§call content must be complete JSON)
"""

import time
from collections.abc import AsyncGenerator
from typing import Any

from ..lib.logger import logger
from .executor import execute
from .persister import EventPersister
from .protocols import ToolCall


class Accumulator:
    """Stream processor focused on event accumulation and tool execution."""

    def __init__(self, config, user_id: str, conversation_id: str, *, chunks: bool = False):
        self.config = config
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.chunks = chunks

        self.persister = EventPersister(conversation_id, user_id, config.storage)

        # Accumulation state
        self.current_type = None
        self.content = ""
        self.start_time = None
        self.end_flushed = False  # Track if we already flushed on §end

    async def process(
        self, parser_events: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process events with clean tool execution."""

        async for event in parser_events:
            event_type = event["type"]
            content = event.get("content", "")
            timestamp = time.time()

            # chunks=True: Yield individual events immediately (AND still accumulate below for tools)
            if self.chunks:
                yield event

            # Control flow events
            if event_type == "execute":
                if self.current_type == "call" and self.content.strip():
                    await self.persister.persist_call(self.content, self.start_time)

                    # Emit call event for display
                    event = {
                        "type": "call",
                        "content": self.content.strip(),
                        "timestamp": self.start_time,
                    }
                    logger.debug(f"EVENT: {event}")
                    yield event

                    # Execute tool and persist result
                    try:
                        tool_call = ToolCall.from_json(self.content.strip())
                        result = await execute(
                            tool_call, self.config, self.user_id, self.conversation_id
                        )

                        from ..tools.format import format_result_human

                        result_content = format_result_human(result)
                        await self.persister.persist_result(result_content, timestamp)

                        event = {
                            "type": "result",
                            "content": result_content,
                            "timestamp": timestamp,
                        }
                        logger.debug(f"EVENT: {event}")
                        yield event
                    except (ValueError, TypeError, KeyError) as e:
                        # JSON parsing error - send feedback to LLM
                        error_content = f"Invalid tool call: {str(e)}"
                        await self.persister.persist_result(error_content, timestamp)

                        yield {
                            "type": "result",
                            "content": error_content,
                            "timestamp": timestamp,
                        }
                    # System errors (OSError, ConnectionError) bubble up

                    # Reset accumulation state
                    self.current_type = None
                    self.content = ""
                    self.start_time = None
                continue

            elif event_type == "end":
                # Flush any accumulated content before emitting end signal
                if self.current_type and self.content.strip():
                    # Persist final events
                    if self.current_type == "think":
                        await self.persister.persist_think(self.content, self.start_time)
                    elif self.current_type == "respond":
                        await self.persister.persist_respond(self.content, self.start_time)

                    # Emit accumulated content (non-chunks mode, skip calls)
                    if not self.chunks and self.current_type != "call":
                        accumulated_event = {
                            "type": self.current_type,
                            "content": self.content.strip(),
                            "timestamp": self.start_time,
                        }
                        logger.debug(f"EVENT: {accumulated_event}")
                        yield accumulated_event

                    self.end_flushed = True  # Mark as flushed

                # Control signal - yield end event then terminate
                yield event  # Original parser event
                break

            # State transitions
            if event_type != self.current_type:
                # Flush accumulated content from previous state
                if self.current_type and self.content.strip():
                    if self.current_type == "think":
                        await self.persister.persist_think(self.content, self.start_time)
                    elif self.current_type == "respond":
                        await self.persister.persist_respond(self.content, self.start_time)

                    # Emit accumulated event (semantic mode only, calls handled by execute)
                    if not self.chunks and self.current_type != "call":
                        yield {
                            "type": self.current_type,
                            "content": self.content.strip(),
                            "timestamp": self.start_time,
                        }

                self.current_type = event_type
                self.content = content
                self.start_time = timestamp
            else:
                # Same type - continue accumulating
                self.content += content

        # Final flush (only reached if stream ends without §end - should be rare)
        if self.current_type and self.content.strip() and not self.end_flushed:
            # Persist final events
            if self.current_type == "think":
                await self.persister.persist_think(self.content, self.start_time)
            elif self.current_type == "respond":
                await self.persister.persist_respond(self.content, self.start_time)

            # Emit final event (non-chunks mode, skip calls)
            if not self.chunks and self.current_type != "call":
                yield {
                    "type": self.current_type,
                    "content": self.content.strip(),
                    "timestamp": self.start_time,
                }
