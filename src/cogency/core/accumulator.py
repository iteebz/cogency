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

import json
import time
from collections.abc import AsyncGenerator

from ..lib.logger import logger
from ..tools.parse import parse_tool_call
from .config import Execution
from .exceptions import ProtocolError
from .executor import execute_tool
from .persister import EventPersister
from .protocols import Event, event_content, event_type


class Accumulator:
    """Stream processor focused on event accumulation and tool execution."""

    def __init__(
        self,
        user_id: str,
        conversation_id: str,
        *,
        execution: Execution,
        chunks: bool = False,
    ):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.chunks = chunks

        self._execution = execution

        self.persister = EventPersister(conversation_id, user_id, execution.storage)

        # Accumulation state
        self.current_type = None
        self.content = ""
        self.start_time = None
        self.end_flushed = False  # Track if we already flushed on §end

    async def process(
        self, parser_events: AsyncGenerator[Event, None]
    ) -> AsyncGenerator[Event, None]:
        """Process events with clean tool execution."""

        async for event in parser_events:
            ev_type = event_type(event)
            content = event_content(event)
            timestamp = time.time()

            # chunks=True: Yield individual events immediately (AND still accumulate below for tools)
            if self.chunks:
                yield event

            # Control flow events
            if ev_type == "execute":
                if self.current_type == "call" and self.content.strip():
                    # Parse tool call and wrap in array for formatter compatibility
                    try:
                        tool_call = parse_tool_call(self.content.strip())
                        call_array = [{"name": tool_call.name, "args": tool_call.args}]
                        await self.persister.persist_call(json.dumps(call_array), self.start_time)
                    except (json.JSONDecodeError, KeyError, ProtocolError) as e:
                        logger.warning(f"Failed to parse tool call JSON: {e}")
                        # Fallback: persist as-is for debugging
                        await self.persister.persist_call(self.content.strip(), self.start_time)

                    # Emit call event for display
                    call_event = {
                        "type": "call",
                        "content": self.content.strip(),
                        "timestamp": self.start_time,
                    }
                    logger.debug(f"EVENT: {call_event}")
                    yield call_event

                    # Execute tool and persist result
                    try:
                        tool_call = parse_tool_call(self.content.strip())
                        result = await execute_tool(
                            tool_call,
                            execution=self._execution,
                            user_id=self.user_id,
                            conversation_id=self.conversation_id,
                        )

                        # Persist the raw ToolResult object as JSON
                        result_json = json.dumps(result.__dict__)
                        await self.persister.persist_result(result_json, timestamp)

                        # Yield a pure event with the structured data in the payload
                        event = {
                            "type": "result",
                            "payload": {
                                "outcome": result.outcome,
                                "content": result.content,
                            },
                            "timestamp": timestamp,
                        }
                        logger.debug(f"EVENT: {event}")
                        yield event
                    except (ValueError, TypeError, KeyError, ProtocolError) as e:
                        # JSON parsing error - send feedback to LLM
                        error_outcome = (
                            f"Invalid tool call: {str(e)}. Original: {self.content.strip()}"
                        )
                        await self.persister.persist_result(error_outcome, timestamp)

                        yield {
                            "type": "result",
                            "payload": {
                                "outcome": error_outcome,
                                "content": "",
                            },
                            "timestamp": timestamp,
                        }
                    # System errors (OSError, ConnectionError) bubble up

                    # Reset accumulation state
                    self.current_type = None
                    self.content = ""
                    self.start_time = None
                continue

            elif ev_type == "end":
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
            if ev_type != self.current_type:
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

                self.current_type = ev_type
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
