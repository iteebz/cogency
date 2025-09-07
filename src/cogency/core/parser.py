"""Token stream parser: state machine → semantic events → persistence."""

import json
import logging
import re
import time
from collections.abc import AsyncGenerator
from typing import Any

from .protocols import DELIMITER, Event
from .result import Err, Ok, Result

logger = logging.getLogger(__name__)


def _parse_json(content: str) -> Result[dict]:
    """Parse JSON content with Result pattern."""
    try:
        json_str = content.strip()
        if not json_str.isascii():
            raise ValueError("Non-ASCII characters")
        return Ok(json.loads(json_str))
    except (json.JSONDecodeError, ValueError) as e:
        return Err(str(e))


def _save_if_needed(event: dict, on_complete) -> None:
    """Save event via callback if provided."""
    if on_complete:
        from ..lib.resilience import safe_callback

        safe_callback(on_complete, event)


def _make_event(event_type, content: str, timestamp: float = None) -> dict:
    """Create standard event dict."""
    return {
        "type": event_type.value,
        "content": content.strip() if content else "",
        "timestamp": timestamp or time.time(),
    }


def _build_pattern():
    """Build regex pattern from Event enum."""
    events = "|".join(
        event.upper() for event in [Event.THINK, Event.CALLS, Event.RESPOND, Event.YIELD]
    )
    return re.compile(rf"{DELIMITER}({events})(?:\s|$)")


def _accumulate_content(buffer: str, content: str, timestamp: float):
    """Accumulate content with timestamp tracking."""
    timestamp = timestamp or time.time()
    return content + buffer, timestamp


def _emit_yield_event(context_state: Event):
    """Emit context-aware YIELD event."""
    if context_state == Event.CALLS:
        context = "execute"  # Yield after calls = execute tools
    elif context_state == Event.RESPOND:
        context = "complete"  # Yield after respond = complete conversation
    else:
        context = "unknown"  # Default yield

    return _make_event(Event.YIELD, context)


def _handle_partial_delimiter(buffer: str, content: str, timestamp: float):
    """Handle incomplete delimiter in buffer - extract content before delimiter."""
    pos = buffer.find(DELIMITER)
    if pos != -1:
        content, timestamp = _accumulate_content(buffer[:pos], content, timestamp)
        return content, timestamp, buffer[pos:]
    content, timestamp = _accumulate_content(buffer, content, timestamp)
    return content, timestamp, ""


def _process_complete_delimiter(match, buffer: str):
    """Process found delimiter and return parsed components."""
    before = buffer[: match.start()]
    delimiter_name = match.group(1).lower()
    delimiter = Event(delimiter_name)
    remaining_buffer = buffer[match.end() :]
    return before, delimiter, remaining_buffer


def _has_potential_delimiter_start(buffer: str) -> bool:
    """Check if buffer ends with potential delimiter start to avoid premature emission."""
    if not buffer:
        return False

    # Check if buffer ends with partial delimiter symbol
    if buffer.endswith("§"):
        return True

    # Check if buffer ends with partial delimiter keywords
    delimiter_keywords = ["THINK", "CALLS", "RESPOND", "YIELD"]
    for keyword in delimiter_keywords:
        for i in range(1, len(keyword)):
            partial = "§" + keyword[:i]
            if buffer.endswith(partial):
                return True

    return False


async def parse_stream(
    tokens: AsyncGenerator, on_complete=None
) -> AsyncGenerator[dict[str, Any], None]:
    """Parse token stream into semantic events with real-time streaming."""
    buffer = ""
    state = Event.THINK
    timestamp = None

    pattern = _build_pattern()

    # Pure string token stream - no Result unwrapping needed
    async for token in tokens:
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")

        logger.debug(f"Parser token: {token[:50]}...")
        buffer += token
        logger.debug(f"Parser buffer: {buffer[:100]}...")

        # Process all complete delimiters in buffer (preserve original logic)
        while True:
            match = pattern.search(buffer)
            if match:
                logger.debug(f"Parser delimiter match: {match.group(1)}")
            else:
                logger.debug("Parser no delimiter match")
            if not match:
                # No complete delimiter - emit or accumulate based on state
                if state == Event.CALLS:
                    # CALLS: keep accumulating for JSON parsing (don't emit)
                    pass
                else:
                    # THINK/RESPOND: stream tokens immediately (pure real-time)
                    if not _has_potential_delimiter_start(buffer):
                        if buffer.strip():
                            event = _make_event(state, buffer, timestamp or time.time())
                            yield event
                        buffer = ""
                break

            # Found complete delimiter - extract components
            before, delimiter, buffer = _process_complete_delimiter(match, buffer)

            # Stream content before delimiter (except CALLS which we parse as JSON)
            if before.strip():
                if state == Event.CALLS:
                    # Parse accumulated CALLS content as JSON
                    result = _parse_json(before)
                    if result.success:
                        event = _make_event(Event.CALLS, before, timestamp or time.time())
                        event["calls"] = result.unwrap()
                        yield event
                        _save_if_needed(event, on_complete)
                    else:
                        yield {"type": "error", "content": f"Invalid JSON: {result.error}"}
                else:
                    # THINK/RESPOND: stream immediately
                    event = _make_event(state, before, timestamp or time.time())
                    yield event

            # Handle context-aware YIELD delimiter
            if delimiter == Event.YIELD:
                yield _emit_yield_event(state)

            # Transition to new state
            state = delimiter
            timestamp = time.time()

    # Final flush of remaining content
    if buffer.strip():
        if state == Event.CALLS:
            # Parse final CALLS JSON
            result = _parse_json(buffer)
            event = _make_event(Event.CALLS, buffer, timestamp or time.time())
            if result.success:
                event["calls"] = result.unwrap()
            yield event
            _save_if_needed(event, on_complete)
        else:
            # Stream final THINK/RESPOND content
            event = _make_event(state, buffer, timestamp or time.time())
            yield event


async def collect_events(stream, on_complete=None) -> list[dict[str, Any]]:
    """Helper: collect all events."""
    events = []
    async for event in parse_stream(stream, on_complete):
        events.append(event)
    return events
