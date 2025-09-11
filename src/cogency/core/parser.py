"""Token stream parser: state machine → semantic events → persistence."""

import json
import logging
import re
import time
from collections.abc import AsyncGenerator
from typing import Any

from ..lib.resilience import safe_callback
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


def _build_pattern():
    """Build regex pattern from Event enum."""
    events = "|".join(
        event.upper()
        for event in [Event.THINK, Event.CALLS, Event.RESPOND, Event.EXECUTE, Event.END]
    )
    return re.compile(rf"{DELIMITER}({events})(?::?\s|:?$)")


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
    delimiter_keywords = ["THINK", "CALLS", "RESPOND", "EXECUTE", "END"]
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
    state = Event.RESPOND
    timestamp = None

    pattern = _build_pattern()

    # Pure string token stream - no Result unwrapping needed
    async for token in tokens:
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")

        # Parser handles semantic events only - no token streaming here

        # Standard parser - no token-level streaming

        buffer += token

        # Process all complete delimiters in buffer (preserve original logic)
        while True:
            match = pattern.search(buffer)
            if not match:
                # No complete delimiter - only accumulate for CALLS
                if state == Event.CALLS:
                    pass
                # For THINK/RESPOND, tokens already streamed above
                break

            # Found complete delimiter - extract components
            before, delimiter, buffer = _process_complete_delimiter(match, buffer)

            # Stream content before delimiter (except CALLS which we parse as JSON)
            if before.strip():
                if state == Event.CALLS:
                    # Parse accumulated CALLS content as JSON
                    result = _parse_json(before)
                    if result.success:
                        event = {
                            "type": Event.CALLS.value,
                            "content": before.strip(),
                            "timestamp": timestamp or time.time(),
                            "calls": result.unwrap(),
                        }
                        yield event
                        if on_complete:
                            safe_callback(on_complete, event)
                    else:
                        yield {"type": "error", "content": f"Invalid JSON: {result.error}"}
                else:
                    # THINK/RESPOND: stream immediately, clean delimiter artifacts
                    content = before.strip()
                    if content.startswith(":"):
                        content = content[1:].strip()
                    yield {
                        "type": state.value,
                        "content": content,
                        "timestamp": timestamp or time.time(),
                    }

            # Handle EXECUTE delimiter
            if delimiter == Event.EXECUTE:
                yield {"type": Event.EXECUTE.value, "content": "", "timestamp": time.time()}

            # Handle END delimiter - emit and terminate
            elif delimiter == Event.END:
                yield {
                    "type": Event.END.value,
                    "content": "",
                    "timestamp": timestamp or time.time(),
                }

            # Transition to new state
            state = delimiter
            timestamp = time.time()

    # Final flush of remaining content
    if buffer.strip():
        if state == Event.CALLS:
            # Parse final CALLS JSON
            result = _parse_json(buffer)
            event = {
                "type": Event.CALLS.value,
                "content": buffer.strip(),
                "timestamp": timestamp or time.time(),
            }
            if result.success:
                event["calls"] = result.unwrap()
            yield event
            if on_complete:
                safe_callback(on_complete, event)
        elif state is not None:
            yield {
                "type": state.value,
                "content": buffer.strip(),
                "timestamp": timestamp or time.time(),
            }
        else:
            yield {
                "type": Event.RESPOND.value,
                "content": buffer.strip(),
                "timestamp": timestamp or time.time(),
            }



async def collect_events(stream, on_complete=None) -> list[dict[str, Any]]:
    """Helper: collect all events."""
    events = []
    async for event in parse_stream(stream, on_complete):
        events.append(event)
    return events
