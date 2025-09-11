"""Token parser: delimiters → events."""

import re
import time
from collections.abc import AsyncGenerator
from typing import Any

from .protocols import DELIMITER


def _build_delimiter_pattern():
    events = "|".join(["THINK", "CALL", "RESPOND", "EXECUTE", "END"])
    return re.compile(rf"{DELIMITER}({events})(?::?\s*|:?$)")


async def parse_tokens(
    token_stream: AsyncGenerator[str, None],
) -> AsyncGenerator[dict[str, Any], None]:
    """Tokens → semantic events."""
    buffer = ""
    current_state = "respond"
    pattern = _build_delimiter_pattern()

    async for token in token_stream:
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")

        # Check for delimiter in this token
        buffer += token
        match = pattern.search(buffer)

        if match:
            # Found delimiter - extract content before it
            content_before = buffer[: match.start()]
            delimiter_name = match.group(1).lower()
            new_state = delimiter_name

            # Emit content before delimiter with current state
            if content_before:
                yield {"type": current_state, "content": content_before, "timestamp": time.time()}

            # Emit delimiter events
            if new_state == "execute":
                yield {"type": "execute", "content": "", "timestamp": time.time()}
            elif new_state == "end":
                yield {"type": "end", "content": "", "timestamp": time.time()}
                return

            # Update sticky note state and reset buffer
            current_state = new_state
            buffer = buffer[match.end() :]

            # Process remaining buffer content if any
            if buffer:
                yield {"type": current_state, "content": buffer, "timestamp": time.time()}
                buffer = ""
        else:
            # No delimiter found - emit token with current sticky note state
            if token:
                yield {"type": current_state, "content": token, "timestamp": time.time()}
            buffer = ""  # Reset buffer after emission
