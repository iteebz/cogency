"""Streaming parser for §-delimited agent protocol."""

from __future__ import annotations

import re
from collections.abc import AsyncGenerator

from ..lib.logger import logger
from .protocols import Event

CONTENT_DELIMITERS = ("think", "call", "respond")
CONTROL_DELIMITERS = ("execute", "end")
DEFAULT_CONTENT_TYPE = "respond"

_DELIMITER_PATTERN = re.compile(
    r"§(?P<name>think|call|respond):\s*|§(?P<control>execute|end)",
    re.IGNORECASE,
)

_DELIMITER_TOKENS = ["§think:", "§call:", "§respond:", "§execute", "§end"]


def _pending_delimiter_start(buffer: str) -> int | None:
    """Return index where a partial delimiter begins, if any."""
    lower = buffer.lower()
    for index, char in enumerate(lower):
        if char != "§":
            continue
        remainder = lower[index:]
        if any(token.startswith(remainder) for token in _DELIMITER_TOKENS):
            return index
    return None


def _emit_content(
    chunk: str,
    current_type: str | None,
    pending_ws: str,
) -> tuple[Event | None, str, str | None]:
    """Prepare a content event if the chunk carries signal."""
    if not chunk:
        return None, pending_ws, current_type

    if not chunk.strip():
        return None, pending_ws + chunk, current_type

    stripped_leading = chunk.lstrip()
    if stripped_leading.startswith("§"):
        lower_candidate = stripped_leading.lower()
        if not any(lower_candidate.startswith(token) for token in _DELIMITER_TOKENS):
            pending_ws = ""
            tail = stripped_leading[1:]
            tail = "".join(tail.split())
            chunk = "§" + tail

    content_type = current_type or DEFAULT_CONTENT_TYPE
    content = pending_ws + chunk
    pending_ws = ""
    event: Event = {"type": content_type, "content": content}
    return event, pending_ws, content_type


async def parse_tokens(token_stream: AsyncGenerator[str, None]) -> AsyncGenerator[Event, None]:
    """Transform raw token stream into structured protocol events."""

    buffer = ""
    current_type: str | None = None
    pending_ws = ""

    async for token in token_stream:
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")

        logger.debug(f"TOKEN: {repr(token)}")
        buffer += token

        while True:
            match = _DELIMITER_PATTERN.search(buffer)
            if not match:
                break

            prefix = buffer[: match.start()]
            buffer = buffer[match.end() :]

            event, pending_ws, current_type = _emit_content(prefix, current_type, pending_ws)
            if event:
                yield event

            control = match.group("control")
            if control:
                control_type = control.lower()
                yield {"type": control_type}
                if control_type == "end":
                    return
                current_type = None
                pending_ws = ""
                continue

            name = match.group("name")
            if name is None:
                continue
            current_type = name.lower()
            pending_ws = ""

        if not buffer:
            continue

        partial_idx = _pending_delimiter_start(buffer)
        if partial_idx is None:
            chunk, buffer = buffer, ""
        else:
            chunk, buffer = buffer[:partial_idx], buffer[partial_idx:]

        event, pending_ws, current_type = _emit_content(chunk, current_type, pending_ws)
        if event:
            yield event

    if buffer:
        event, pending_ws, current_type = _emit_content(buffer, current_type, pending_ws)
        if event:
            yield event
