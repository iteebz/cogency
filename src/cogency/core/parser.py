"""Token-based streaming parser for delimiter protocol.

Core responsibilities:
1. Delimiter detection: Recognize §respond:, §think:, etc. across token boundaries
2. Type labeling: Assign event type to subsequent content tokens
3. Control emission: Emit §end, §execute as state boundaries for accumulator
4. Delimiter filtering: Remove delimiter tokens from output stream

Simple token-to-event mapping - accumulator handles content accumulation.
"""

from collections.abc import AsyncGenerator
from typing import Any

VALID_TYPES = {"think", "call", "respond", "execute", "end"}


async def _preprocess_tokens(token_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """Split complex tokens with multiple delimiters into simple tokens."""
    async for token in token_stream:
        if not isinstance(token, str):
            yield token  # Pass through non-string tokens for error handling
        elif "\n§" in token:
            # Split tokens containing newline + delimiter
            parts = token.split("\n§")
            yield parts[0] + "\n"  # First part with preserved newline
            for part in parts[1:]:
                yield "§" + part  # Each delimiter part
        else:
            yield token


async def parse_tokens(
    token_stream: AsyncGenerator[str, None],
) -> AsyncGenerator[dict[str, Any], None]:
    """Transform token stream into labeled events via delimiter detection.

    Yields:
    - Content events: {"type": "think|call|respond", "content": str}
    - Control events: {"type": "execute|end"}
    """
    delimiter_buffer = ""
    current_type = None  # Must be set by first delimiter

    async for token in _preprocess_tokens(token_stream):
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")

        from ..lib.logger import logger

        logger.debug(f"TOKEN: {repr(token)}")

        # Delimiter processing - continue building if we have partial delimiter
        if delimiter_buffer or token.strip().startswith("§"):
            # For embedded delimiter preservation, use original token if single token
            original_token = token
            delimiter_buffer += token.strip()

            # Check for complete delimiter
            if ":" in delimiter_buffer and delimiter_buffer.startswith("§"):
                # Extract type and content
                colon_pos = delimiter_buffer.find(":")
                delimiter_type = delimiter_buffer[1:colon_pos].lower()

                # Use original token for content if it's a single token with embedded delimiters
                if ":" in original_token and original_token.strip().startswith("§"):
                    orig_colon_pos = original_token.find(":")
                    content_part = original_token[orig_colon_pos + 1 :].lstrip()
                else:
                    content_part = delimiter_buffer[colon_pos + 1 :].lstrip()

                if delimiter_type in VALID_TYPES:
                    if delimiter_type == "end":
                        event = {"type": "end"}
                        yield event
                        return  # Terminate immediately
                    elif delimiter_type == "execute":
                        yield {"type": "execute"}
                    else:
                        current_type = delimiter_type
                        if content_part:  # Embedded content - check for more delimiters
                            if "§" in content_part:
                                parts = content_part.split("§", 1)
                                clean_content = parts[0]
                                if clean_content:
                                    yield {"type": current_type, "content": clean_content}
                                # Process remaining delimiter immediately
                                remaining_delimiter = "§" + parts[1]
                                if remaining_delimiter in [f"§{t}" for t in VALID_TYPES]:
                                    delimiter_type = remaining_delimiter[1:].lower()
                                    if delimiter_type in {"execute", "end"}:
                                        yield {"type": delimiter_type}
                                        if delimiter_type == "end":
                                            return
                                elif remaining_delimiter == "§":
                                    # Incomplete delimiter - save for next token
                                    delimiter_buffer = remaining_delimiter
                                    continue
                            else:
                                yield {"type": current_type, "content": content_part}
                    delimiter_buffer = ""
                    continue
                else:
                    # Invalid delimiter - treat as content
                    if current_type is None:
                        current_type = "respond"
                    yield {"type": current_type, "content": delimiter_buffer}
                    delimiter_buffer = ""
                    continue

            # Naked delimiters (only execute and end can be naked)
            elif delimiter_buffer in ["§execute", "§end"]:
                delimiter_type = delimiter_buffer[1:].lower()
                event = {"type": delimiter_type}
                yield event
                if delimiter_type == "end":
                    return
                delimiter_buffer = ""
                continue

            # Check for malformed delimiter (too long without completion)
            elif len(delimiter_buffer) > 10:  # Max valid delimiter is 9 chars (§respond:)
                if current_type is None:
                    current_type = "respond"
                yield {"type": current_type, "content": delimiter_buffer}
                delimiter_buffer = ""
                continue

            # Still building - skip
            continue

        # Content token
        elif token and token != ":":
            # Check if this token completes a partial delimiter in buffer
            if delimiter_buffer == "§" and ":" in token:
                colon_pos = token.find(":")
                delimiter_type = token[:colon_pos].lower()
                if delimiter_type in VALID_TYPES:
                    # Complete delimiter found
                    current_type = delimiter_type
                    content_part = token[colon_pos + 1 :].lstrip()
                    delimiter_buffer = ""

                    # Handle embedded delimiters (simple case only)
                    if "§" in content_part:
                        parts = content_part.split("§", 1)
                        if parts[0]:
                            yield {"type": current_type, "content": parts[0]}
                        remaining_delimiter = "§" + parts[1]
                        if remaining_delimiter in [f"§{t}" for t in VALID_TYPES]:
                            delimiter_type = remaining_delimiter[1:].lower()
                            if delimiter_type in {"execute", "end"}:
                                yield {"type": delimiter_type}
                                if delimiter_type == "end":
                                    return
                        elif remaining_delimiter == "§":
                            delimiter_buffer = remaining_delimiter
                    else:
                        if content_part:
                            yield {"type": current_type, "content": content_part}
                    continue

            if current_type is None:
                current_type = "respond"

            # Handle embedded delimiters in content
            if "§" in token:
                parts = token.split("§", 1)
                content_part = parts[0]

                # Yield content if exists
                if content_part:
                    yield {"type": current_type, "content": content_part}

                # Process remaining delimiter immediately
                remaining_delimiter = "§" + parts[1]
                if remaining_delimiter in [f"§{t}" for t in VALID_TYPES]:
                    delimiter_type = remaining_delimiter[1:].lower()
                    if delimiter_type in {"execute", "end"}:
                        yield {"type": delimiter_type}
                        if delimiter_type == "end":
                            return
                continue

            yield {"type": current_type, "content": token}
