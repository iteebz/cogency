"""Pure token parser: delimiter detection → semantic events.

ZEALOT ARCHITECTURE: Parser does ONE job - convert raw tokens to semantic events.
No accumulation, no state management, no DB writes. Pure function.

Streamer (separate component) handles:
- Event accumulation and state transitions
- Database persistence  
- Tool coordination
- Consumer event formatting

This separation keeps parser simple, testable, and fast.
"""

import re
import time
from collections.abc import AsyncGenerator
from typing import Any

from .protocols import DELIMITER, Event


def _build_delimiter_pattern():
    """Build regex pattern for delimiter detection."""
    events = "|".join(
        event.upper() 
        for event in [Event.THINK, Event.CALL, Event.RESPOND, Event.EXECUTE, Event.END]
    )
    return re.compile(rf"{DELIMITER}({events})(?::?\s*|:?$)")


async def parse_tokens(
    token_stream: AsyncGenerator[str, None]
) -> AsyncGenerator[dict[str, Any], None]:
    """PURE parser: tokens → events with sticky note state.
    
    Just adds semantic type to each token based on current delimiter state.
    NO accumulation, NO content processing - just sticky notes.
    
    Event format:
    {
        "type": "think" | "call" | "respond" | "execute" | "end", 
        "content": str,  # Raw token content
        "timestamp": float
    }
    """
    buffer = ""
    current_state = Event.RESPOND  # Sticky note state
    pattern = _build_delimiter_pattern()
    
    async for token in token_stream:
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")
            
        # Check for delimiter in this token
        buffer += token
        match = pattern.search(buffer)
        
        if match:
            # Found delimiter - extract content before it
            content_before = buffer[:match.start()]
            delimiter_name = match.group(1).lower() 
            new_state = Event(delimiter_name)
            
            # Emit content before delimiter with current state
            if content_before:
                yield {
                    "type": current_state.value,
                    "content": content_before,
                    "timestamp": time.time()
                }
            
            # Emit delimiter events
            if new_state == Event.EXECUTE:
                yield {
                    "type": Event.EXECUTE.value,
                    "content": "",
                    "timestamp": time.time()
                }
            elif new_state == Event.END:
                yield {
                    "type": Event.END.value,
                    "content": "", 
                    "timestamp": time.time()
                }
                return
            
            # Update sticky note state and reset buffer
            current_state = new_state
            buffer = buffer[match.end():]
            
            # Process remaining buffer content if any
            if buffer:
                yield {
                    "type": current_state.value,
                    "content": buffer,
                    "timestamp": time.time()
                }
                buffer = ""
        else:
            # No delimiter found - emit token with current sticky note state
            if token:
                yield {
                    "type": current_state.value,
                    "content": token,
                    "timestamp": time.time()
                }
            buffer = ""  # Reset buffer after emission