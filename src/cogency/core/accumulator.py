"""Event accumulator: accumulate → execute → persist.

Algorithm:
1. Accumulate content until type changes or control event (execute/end)
2. On execute: run pending tool calls, emit results
3. Persist all events to storage

Modes: token (stream respond/think chunks), event (complete semantic units).
"""

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Literal

from .circuit import CircuitBreaker
from .codec import format_results_array, parse_tool_call
from .config import Execution
from .executor import execute_tools
from .protocols import (
    CallEvent,
    EndEvent,
    Event,
    ExecuteEvent,
    RespondEvent,
    ResultEvent,
    ThinkEvent,
    ToolCall,
    ToolResult,
    event_content,
    event_type,
)

logger = logging.getLogger(__name__)

# Conversation events that get persisted to storage
# "user" omitted - handled by resume/replay before agent stream
PERSISTABLE_EVENTS = {"think", "call", "result", "respond"}

# Events with content that can be accumulated over multiple parser chunks
AccumulatableEvent = ThinkEvent | CallEvent | RespondEvent | ResultEvent
AccumulatableType = Literal["think", "call", "respond", "result"]


class Accumulator:
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
        self.current_type: AccumulatableType | None = None
        self.content = ""
        self.start_time: float | None = None

        # Batch execution state for multi-tool blocks
        self.pending_calls: list[ToolCall] = []
        self.call_timestamps: list[float] = []

    async def _flush_accumulated(self) -> AccumulatableEvent | None:
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
        if self.stream == "event" and self.current_type != "call" and self.start_time is not None:
            ts = time.time()
            if self.current_type == "think":
                return ThinkEvent(type="think", content=clean_content, timestamp=ts)
            elif self.current_type == "respond":
                return RespondEvent(type="respond", content=clean_content, timestamp=ts)
            elif self.current_type == "result":
                return ResultEvent(type="result", content=clean_content, timestamp=ts, payload=None)
        return None

    async def _handle_execute(self, timestamp: float) -> AsyncGenerator[Event, None]:
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
                ToolResult(outcome=f"Tool execution failed: {e!s}", content="", error=True)
                for _ in self.pending_calls
            ]

        for result in results:
            if result.error:
                self.circuit_breaker.record_failure()
            else:
                self.circuit_breaker.record_success()

        if self.circuit_breaker.is_open():
            yield ResultEvent(
                type="result",
                payload={
                    "outcome": "Max failures. Terminating.",
                    "content": "",
                    "error": True,
                },
                content="Max failures. Terminating.",
                timestamp=timestamp,
            )
            yield EndEvent(type="end", timestamp=timestamp)
            self.pending_calls = []
            self.call_timestamps = []
            return

        clean_results = format_results_array(self.pending_calls, results)
        await self.storage.save_message(
            self.conversation_id, self.user_id, "result", clean_results, timestamp
        )

        yield ResultEvent(
            type="result",
            payload={
                "tools_executed": len(results),
                "success_count": sum(1 for r in results if not r.error),
                "failure_count": sum(1 for r in results if r.error),
            },
            content=clean_results,
            timestamp=timestamp,
        )

        self.pending_calls = []
        self.call_timestamps = []

    async def process(  # noqa: C901  # event accumulator state machine with tool execution
        self, parser_events: AsyncGenerator[Event, None]
    ) -> AsyncGenerator[Event, None]:
        async for event in parser_events:
            ev_type = event_type(event)
            content = event_content(event)
            timestamp = time.time()

            # Handle calls immediately (parser guarantees complete JSON)
            if ev_type == "call":
                try:
                    tool_call = parse_tool_call(content)
                    call_json = json.dumps({"name": tool_call.name, "args": tool_call.args})

                    await self.storage.save_message(
                        self.conversation_id, self.user_id, "call", call_json, timestamp
                    )
                    self.pending_calls.append(tool_call)
                    self.call_timestamps.append(timestamp)

                    yield CallEvent(type="call", content=call_json, timestamp=timestamp)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse tool call: {e}")

                continue

            # Handle execute - flush any non-call accumulation and execute batch
            if ev_type == "execute":
                if self.current_type and self.content.strip():
                    flushed = await self._flush_accumulated()
                    if flushed:
                        yield flushed
                    self.current_type = None
                    self.content = ""
                    self.start_time = None

                yield ExecuteEvent(type="execute", timestamp=timestamp)
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

                # Emit end and terminate with fresh timestamp
                yield EndEvent(type="end", timestamp=time.time())
                return

            # Handle type transitions (non-call, non-control events)
            if ev_type != self.current_type:
                # Flush previous accumulation
                flushed = await self._flush_accumulated()
                if flushed:
                    yield flushed

                # Start new accumulation (only for accumulatable types)
                if ev_type in ("think", "call", "respond", "result"):
                    self.current_type = ev_type
                    self.content = content
                    self.start_time = timestamp
            else:
                # Continue accumulating same type
                self.content += content

            # stream="token": Yield respond/think chunks while accumulating for persistence
            if self.stream == "token" and ev_type in ("respond", "think"):
                yield event

        # Stream ended without explicit end event - flush remaining content
        flushed = await self._flush_accumulated()
        if flushed:
            yield flushed
