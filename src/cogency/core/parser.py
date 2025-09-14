"""Word-boundary streaming parser with delimiter protocol.

Transforms character streams into semantic events via word-boundary detection.
Handles LLM protocol violations (compact JSON, split delimiters) robustly.

Core strategy: Buffer characters until whitespace, detect delimiters on complete words.
"""

import re
from collections.abc import AsyncGenerator
from typing import Any

DELIMITER = "§"


def _delimiter_pattern():
    """Compile regex for delimiter detection on word boundaries."""
    events = "|".join(["THINK", "CALL", "RESPOND", "EXECUTE", "END"])
    return re.compile(rf"^{DELIMITER}({events})(?::.*)?$")


def _process_word(word: str, current_state: str, delimiter_pattern) -> tuple[str, list[dict]]:
    """Process complete word for delimiter detection and event emission.

    Handles compact JSON (§CALL:{"name":"tool"}) by splitting at colon boundary.
    Returns updated state and list of events to emit.
    """
    events = []

    if word.startswith(DELIMITER):
        # Extract delimiter and content
        colon_pos = word.find(":")
        if colon_pos > 0:
            delimiter_part = word[: colon_pos + 1]
            content_part = word[colon_pos + 1 :]
        else:
            delimiter_part = word
            content_part = ""

        # Check if valid delimiter
        if match := delimiter_pattern.match(delimiter_part):
            delimiter_name = match.group(1).lower()

            if delimiter_name == "execute":
                events.append({"type": "execute", "content": ""})
            elif delimiter_name == "end":
                events.append({"type": "end", "content": ""})
            else:
                # State transition
                current_state = delimiter_name
                if content_part.strip():
                    events.append(
                        {
                            "type": current_state,
                            "content": content_part.strip(),
                        }
                    )
        else:
            # Invalid delimiter, treat as content
            events.append({"type": current_state, "content": word})
    else:
        # Regular content
        events.append({"type": current_state, "content": word})

    return current_state, events


async def parse_tokens(
    token_stream: AsyncGenerator[str, None],
) -> AsyncGenerator[dict[str, Any], None]:
    """Transform character stream into semantic events via word-boundary parsing.

    Buffers characters until whitespace, then processes complete words for delimiter
    detection. Handles LLM protocol violations robustly while maintaining accuracy.

    Yields events: {"type": "think|call|respond|execute|end", "content": str}
    """
    word_buffer = ""
    current_state = "respond"
    delimiter_pattern = _delimiter_pattern()

    async for token in token_stream:
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")

        for char in token:
            if char.isspace():
                # Word boundary reached - process accumulated word
                if word_buffer.strip():
                    word = word_buffer.strip()
                    current_state, events = _process_word(word, current_state, delimiter_pattern)

                    for event in events:
                        yield event
                        if event["type"] == "end":
                            return  # Terminate on END

                word_buffer = ""
            else:
                word_buffer += char

    # Process final word if stream ends without whitespace
    if word_buffer.strip():
        word = word_buffer.strip()
        current_state, events = _process_word(word, current_state, delimiter_pattern)

        for event in events:
            yield event
