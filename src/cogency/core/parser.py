from __future__ import annotations

import logging
import re
from collections.abc import AsyncGenerator

from .protocols import Event

logger = logging.getLogger(__name__)


async def _wrap_string(text: str) -> AsyncGenerator[str, None]:
    """Wrap complete string as single-yield generator."""
    yield text


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
    idx = lower.find("§")
    while idx != -1:
        remainder = lower[idx:]
        if any(remainder.startswith(token[: len(remainder)]) for token in _DELIMITER_TOKENS):
            return idx
        idx = lower.find("§", idx + 1)
    return None


def _emit_content(chunk: str, current_type: str | None) -> Event | None:
    """Prepare a content event if the chunk carries signal."""
    if not chunk:
        return None
    content_type = current_type or DEFAULT_CONTENT_TYPE
    return {"type": content_type, "content": chunk}


async def parse_tokens(
    token_stream: AsyncGenerator[str, None] | str,
) -> AsyncGenerator[Event, None]:
    """Transform raw token stream or complete string into structured protocol events."""

    if isinstance(token_stream, str):
        token_stream = _wrap_string(token_stream)

    buffer = ""
    current_type: str | None = None

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

            if event := _emit_content(prefix, current_type):
                yield event

            control = match.group("control")
            if control:
                control_type = control.lower()
                yield {"type": control_type}
                if control_type in ("execute", "end"):
                    return
                current_type = None
                continue

            name = match.group("name")
            if name is None:
                continue
            current_type = name.lower()

        if not buffer:
            continue

        partial_idx = _pending_delimiter_start(buffer)
        if partial_idx is None:
            chunk, buffer = buffer, ""
        else:
            chunk, buffer = buffer[:partial_idx], buffer[partial_idx:]

        if event := _emit_content(chunk, current_type):
            yield event

    if buffer and (event := _emit_content(buffer, current_type)):
        yield event
