"""Event accumulator with tool execution and persistence.

Core algorithm:
1. Accumulate content until type changes or control events (§execute, §end)
2. Execute tool calls when §execute encountered
3. Persist all events via specialized EventPersister
4. Streaming modes:
   - stream="token": Stream respond/think naturally, accumulate call/result/cancelled/metric
   - stream="event": Accumulate all, yield complete semantic units on type changes
   Both modes accumulate call content fully (must be complete JSON for execution)
"""

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Literal

from ..lib.resilience import CircuitBreaker
from .codec import parse_tool_call
from .config import Execution
from .executor import execute_tools
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
        stream: Literal["event", "token"] = "event",
        max_failures: int = 3,
    ):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.stream = stream

        self._execution = execution

        self.storage = execution.storage
        self.circuit_breaker = CircuitBreaker(max_failures=max_failures)

        # Accumulation state
        self.current_type = None
        self.content = ""
        self.start_time = None

        # Batch execution state for multi-tool blocks
        self.pending_calls = []  # Accumulated ToolCall objects before execute event
        self.call_timestamps = []  # Preserve timestamps for each call

    async def _flush_accumulated(self) -> Event | None:
        """Flush accumulated content, persist and return event if needed."""
        if not self.current_type or not self.content.strip():
            return None

        # Persist conversation events only (not control flow or metrics)
        clean_content = self.content.strip() if self.stream != "token" else self.content

        if self.current_type in PERSISTABLE_EVENTS:
            await self.storage.save_message(
                self.conversation_id,
                self.user_id,
                self.current_type,
                clean_content,
                self.start_time,
            )

        # Emit event in semantic mode (skip calls - handled by execute)
        if self.stream == "event" and self.current_type != "call":
            return {
                "type": self.current_type,
                "content": clean_content,
                "timestamp": self.start_time,
            }
        return None

    async def _handle_execute(self, timestamp: float) -> AsyncGenerator[Event, None]:
        """Execute batch of tool calls sequentially, maintaining order."""
        if not self.pending_calls:
            return

        try:
            results = await execute_tools(
                self.pending_calls,
                execution=self._execution,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
            )
        except (ValueError, TypeError, KeyError) as e:
            results = [
                ToolResult(outcome=f"Tool execution failed: {str(e)}", content="", error=True)
                for _ in self.pending_calls
            ]

        from .codec import format_result_agent

        for i, result in enumerate(results):
            if result.error:
                self.circuit_breaker.record_failure()
            else:
                self.circuit_breaker.record_success()

            result_ts = self.call_timestamps[i] if i < len(self.call_timestamps) else timestamp

            await self.storage.save_message(
                self.conversation_id, self.user_id, "result", json.dumps(result.__dict__), result_ts
            )

            if self.circuit_breaker.is_open():
                yield {
                    "type": "result",
                    "payload": {
                        "outcome": "Max failures. Terminating.",
                        "content": "",
                        "error": True,
                    },
                    "content": "Max failures. Terminating.",
                    "timestamp": timestamp,
                }
                yield {"type": "end", "timestamp": timestamp}
                self.pending_calls = []
                self.call_timestamps = []
                return

            yield {
                "type": "result",
                "payload": {
                    "outcome": result.outcome,
                    "content": result.content,
                    "error": result.error,
                },
                "content": f"{format_result_agent(result)}",
                "timestamp": result_ts,
            }

        self.pending_calls = []
        self.call_timestamps = []

    async def process(
        self, parser_events: AsyncGenerator[Event, None]
    ) -> AsyncGenerator[Event, None]:
        """Process events with batched tool execution."""

        async for event in parser_events:
            ev_type = event_type(event)
            content = event_content(event)
            timestamp = time.time()

            # Handle control events
            if ev_type == "execute":
                # Handle pending call before execute (don't use _flush_accumulated for calls)
                if self.current_type == "call" and self.content.strip():
                    yield {
                        "type": "call",
                        "content": self.content.strip(),
                        "timestamp": self.start_time,
                    }

                # Parse pending call batch and collect into pending_calls
                if self.current_type == "call" and self.content.strip():
                    try:
                        tool_call = parse_tool_call(self.content.strip())
                        call_json = json.dumps({"name": tool_call.name, "args": tool_call.args})
                        await self.storage.save_message(
                            self.conversation_id, self.user_id, "call", call_json, self.start_time
                        )
                        self.pending_calls.append(tool_call)
                        self.call_timestamps.append(self.start_time)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse tool call: {e}")
                        await self.storage.save_message(
                            self.conversation_id,
                            self.user_id,
                            "call",
                            self.content.strip(),
                            self.start_time,
                        )
                    self.current_type = None
                    self.content = ""
                    self.start_time = None

                # Emit execute and process batch
                yield {"type": "execute", "timestamp": timestamp}
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

            # Handle type transitions (including call events)
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

            # stream="token": Yield respond/think chunks while accumulating for persistence
            if self.stream == "token" and ev_type in ("respond", "think"):
                yield event

        # Stream ended without §end - flush remaining content
        flushed = await self._flush_accumulated()
        if flushed:
            yield flushed
