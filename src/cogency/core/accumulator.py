"""Event accumulator with tool execution and persistence.

Core algorithm:
1. Accumulate content until type changes or control events (§execute, §end)
2. Execute tool calls when §execute encountered
3. Persist all events via specialized EventPersister
4. Streaming modes:
   - chunks=True: Stream respond/think naturally, accumulate call/result/cancelled/metric
   - chunks=False: Accumulate all, yield complete semantic units on type changes
   Both modes accumulate call content fully (must be complete JSON for execution)
"""

import json
import logging
import time
from collections.abc import AsyncGenerator

from ..lib.resilience import CircuitBreaker
from .codec import parse_tool_call
from .config import Execution
from .executor import execute_tool
from .protocols import Event, ToolResult, event_content, event_type

logger = logging.getLogger(__name__)

# Conversation events that get persisted to storage
# "user" omitted - handled by resume/replay before agent stream
PERSISTABLE_EVENTS = {"think", "call", "result", "respond"}


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

        self.storage = execution.storage
        self.circuit_breaker = CircuitBreaker(max_failures=max_failures)

        # Accumulation state
        self.current_type = None
        self.content = ""
        self.start_time = None

    async def _flush_accumulated(self) -> Event | None:
        """Flush accumulated content, persist and return event if needed."""
        if not self.current_type or not self.content.strip():
            return None

        # Persist conversation events only (not control flow or metrics)
        clean_content = self.content.strip() if not self.chunks else self.content

        if self.current_type in PERSISTABLE_EVENTS:
            await self.storage.save_message(
                self.conversation_id,
                self.user_id,
                self.current_type,
                clean_content,
                self.start_time,
            )

        # Emit event in semantic mode (skip calls - handled by execute)
        if not self.chunks and self.current_type != "call":
            return {
                "type": self.current_type,
                "content": clean_content,
                "timestamp": self.start_time,
            }
        return None

    async def _handle_execute(self, timestamp: float) -> AsyncGenerator[Event, None]:
        """Handle tool execution with persistence."""
        if self.current_type != "call" or not self.content.strip():
            return

        call_text = self.content.strip()

        # Parse once, use everywhere
        try:
            tool_call = parse_tool_call(call_text)
            call_json = json.dumps({"name": tool_call.name, "args": tool_call.args})
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse tool call: {e}")
            await self.storage.save_message(
                self.conversation_id, self.user_id, "call", call_text, self.start_time
            )
            yield {"type": "call", "content": call_text, "timestamp": self.start_time}
            yield {"type": "execute", "timestamp": timestamp}
            result = ToolResult(
                outcome=f"Invalid tool call: {str(e)}", content=call_text, error=True
            )
            await self.storage.save_message(
                self.conversation_id, self.user_id, "result", json.dumps(result.__dict__), timestamp
            )
            yield {
                "type": "result",
                "payload": {"outcome": result.outcome, "content": result.content, "error": True},
                "content": f"{result.outcome}",
                "timestamp": timestamp,
            }
            self.current_type = None
            self.content = ""
            self.start_time = None
            return

        # Persist parsed call
        await self.storage.save_message(
            self.conversation_id, self.user_id, "call", call_json, self.start_time
        )

        yield {"type": "call", "content": call_text, "timestamp": self.start_time}
        yield {"type": "execute", "timestamp": timestamp}

        # Execute tool (already parsed)
        try:
            result = await execute_tool(
                tool_call,
                execution=self._execution,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
            )
        except (ValueError, TypeError, KeyError) as e:
            result = ToolResult(outcome=f"Tool execution failed: {str(e)}", content="", error=True)

        # Persist result
        await self.storage.save_message(
            self.conversation_id, self.user_id, "result", json.dumps(result.__dict__), timestamp
        )

        # Track failures for circuit breaker
        if result.error:
            self.circuit_breaker.record_failure()
        else:
            self.circuit_breaker.record_success()

        # Terminate on max failures
        if self.circuit_breaker.is_open():
            termination_result = ToolResult(
                outcome="Max failures. Terminating.", content="", error=True
            )
            yield {
                "type": "result",
                "payload": {"outcome": termination_result.outcome, "content": "", "error": True},
                "content": f"{termination_result.outcome}",
                "timestamp": timestamp,
            }
            yield {"type": "end", "timestamp": timestamp}
            return

        from .codec import format_result_agent

        yield {
            "type": "result",
            "payload": {
                "outcome": result.outcome,
                "content": result.content,
                "error": result.error,
            },
            "content": f"{format_result_agent(result)}",
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

            # chunks=True: Yield respond/think chunks while accumulating for persistence
            if self.chunks and ev_type in ("respond", "think"):
                yield event

        # Stream ended without §end - flush remaining content
        flushed = await self._flush_accumulated()
        if flushed:
            yield flushed
