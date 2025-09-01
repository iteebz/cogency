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


def _extract_token(token_result):
    """Extract token from Result wrapper."""
    if hasattr(token_result, "failure") and token_result.failure:
        return None, token_result.error
    if hasattr(token_result, "unwrap"):
        return token_result.unwrap(), None
    return token_result, None


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
        "type": event_type,
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
    if buffer and not content:
        timestamp = time.time()
    return content + buffer, timestamp


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


async def parse_stream(
    tokens: AsyncGenerator, on_complete=None
) -> AsyncGenerator[dict[str, Any], None]:
    """Parse token stream into semantic events with context-aware yield."""
    buffer = ""
    state = Event.THINK
    content = ""
    timestamp = None

    pattern = _build_pattern()

    async for token_result in tokens:
        token, error = _extract_token(token_result)
        if error:
            yield {"type": "error", "content": error}
            return

        buffer += token

        while True:
            match = pattern.search(buffer)
            if not match:
                # Handle partial delimiters
                content, timestamp, buffer = _handle_partial_delimiter(buffer, content, timestamp)
                break

            # Found complete delimiter
            before, delimiter, buffer = _process_complete_delimiter(match, buffer)

            # Add content before delimiter
            if before:
                content, timestamp = _accumulate_content(before, content, timestamp)

            # Emit current state if we have content
            if content.strip():
                event = _make_event(state, content, timestamp)

                if state == Event.CALLS:
                    result = _parse_json(content)
                    if result.success:
                        event["calls"] = result.unwrap()
                        _save_if_needed(event, on_complete)
                    else:
                        yield {"type": "error", "content": f"Invalid JSON: {result.error}"}
                        # Reset and continue
                        state = delimiter
                        content = ""
                        timestamp = None
                        buffer = buffer[match.end() :]
                        continue

                yield event
                if state in [Event.THINK, Event.RESPOND]:
                    _save_if_needed(event, on_complete)

            # Handle context-aware YIELD delimiter
            if delimiter == Event.YIELD:
                # Determine context from current state
                if state == Event.CALLS:
                    context = "execute"  # Yield after calls = execute tools
                elif state == Event.RESPOND:
                    context = "complete"  # Yield after respond = complete conversation
                else:
                    context = "unknown"  # Default yield

                yield _make_event(Event.YIELD, context)

            # Transition to new state
            state = delimiter
            content = ""
            timestamp = None

    # Final flush
    if content.strip():
        event = _make_event(state, content, timestamp)
        if state == Event.CALLS:
            result = _parse_json(content)
            if result.success:
                event["calls"] = result.unwrap()
        yield event
        _save_if_needed(event, on_complete)


async def collect_events(stream, on_complete=None) -> list[dict[str, Any]]:
    """Helper: collect all events."""
    events = []
    async for event in parse_stream(stream, on_complete):
        events.append(event)
    return events
