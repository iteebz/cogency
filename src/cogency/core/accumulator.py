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
from ..lib.resilience import CircuitBreaker
from ..tools.parse import parse_tool_call
from .config import Execution
from .exceptions import ProtocolError
from .executor import execute_tool
from .persister import EventPersister
from .protocols import Event, ToolResult, event_content, event_type


class Accumulator:
    """Stream processor focused on event accumulation and tool execution."""

    def __init__(
        self,
        user_id: str,
        conversation_id: str,
        *,
        execution: Execution,
        chunks: bool = False,
        max_failures: int = 3,
    ):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.chunks = chunks

        self._execution = execution

        self.persister = EventPersister(conversation_id, user_id, execution.storage)
        self.circuit_breaker = CircuitBreaker(max_failures=max_failures)

        # Accumulation state
        self.current_type = None
        self.content = ""
        self.start_time = None

    async def _flush_accumulated(self) -> Event | None:
        """Flush accumulated content, persist and return event if needed."""
        if not self.current_type or not self.content.strip():
            return None

        # Persist based on type
        if self.current_type == "think":
            await self.persister.persist_think(self.content, self.start_time)
        elif self.current_type == "respond":
            await self.persister.persist_respond(self.content, self.start_time)

        # Emit event in semantic mode (skip calls - handled by execute)
        if not self.chunks and self.current_type != "call":
            return {
                "type": self.current_type,
                "content": self.content.strip(),
                "timestamp": self.start_time,
            }
        return None

    async def _handle_execute(self, timestamp: float) -> AsyncGenerator[Event, None]:
        """Handle tool execution with persistence."""
        if self.current_type != "call" or not self.content.strip():
            return

        call_text = self.content.strip()

        # Parse and persist call
        try:
            tool_call = parse_tool_call(call_text)
            call_array = [{"name": tool_call.name, "args": tool_call.args}]
            await self.persister.persist_call(json.dumps(call_array), self.start_time)
        except (json.JSONDecodeError, KeyError, ProtocolError) as e:
            logger.warning(f"Failed to parse tool call JSON: {e}")
            await self.persister.persist_call(call_text, self.start_time)

        yield {"type": "call", "content": call_text, "timestamp": self.start_time}

        # Execute tool
        try:
            tool_call = parse_tool_call(call_text)
            result = await execute_tool(
                tool_call,
                execution=self._execution,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
            )
        except (ValueError, TypeError, KeyError, ProtocolError) as e:
            result = ToolResult(
                outcome=f"Invalid tool call: {str(e)}", content=call_text, error=True
            )

        await self.persister.persist_result(json.dumps(result.__dict__), timestamp)

        # Track failures
        if result.error:
            self.circuit_breaker.record_failure()
        else:
            self.circuit_breaker.record_success()

        if self.circuit_breaker.is_open():
            yield {
                "type": "result",
                "payload": {"outcome": "Max failures. Terminating.", "content": "", "error": True},
                "timestamp": timestamp,
            }
            yield {"type": "end", "timestamp": timestamp}
            return

        yield {
            "type": "result",
            "payload": {
                "outcome": result.outcome,
                "content": result.content,
                "error": result.error,
            },
            "timestamp": timestamp,
        }

        self.current_type = None
        self.content = ""
        self.start_time = None

    async def process(
        self, parser_events: AsyncGenerator[Event, None]
    ) -> AsyncGenerator[Event, None]:
        """Process events with clean tool execution."""

        async for event in parser_events:
            ev_type = event_type(event)
            content = event_content(event)
            timestamp = time.time()

            # chunks=True: Yield events immediately
            if self.chunks:
                yield event

            # Handle control events
            if ev_type == "execute":
                async for result_event in self._handle_execute(timestamp):
                    yield result_event
                    if event_type(result_event) == "end":
                        return
                continue

            if ev_type == "end":
                # Flush accumulated content before terminating
                flushed = await self._flush_accumulated()
                if flushed:
                    logger.debug(f"EVENT: {flushed}")
                    yield flushed

                # Emit end and terminate
                yield event
                return

            # Handle type transitions
            if ev_type != self.current_type:
                # Flush previous accumulation
                flushed = await self._flush_accumulated()
                if flushed:
                    yield flushed

                # Start new accumulation
                self.current_type = ev_type
                self.content = content
                self.start_time = timestamp
            else:
                # Continue accumulating same type
                self.content += content

        # Stream ended without §end - flush remaining content
        flushed = await self._flush_accumulated()
        if flushed:
            yield flushed
