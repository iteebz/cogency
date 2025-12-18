"""XML protocol parser. THINK → EXECUTE → RESULTS.

Why JSON inside XML markers (not pure XML)?
- Content like "</execute>" in tool args is JSON-escaped, never collides
- LLMs generate JSON naturally, XML attribute escaping is awkward
- Standard JSON parsing, no custom escape rules
"""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

from .errors import ProtocolError
from .protocols import Event, ToolCall

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

TAG_PATTERN = {
    "think": ("<think>", "</think>"),
    "execute": ("<execute>", "</execute>"),
    "results": ("<results>", "</results>"),
    "end": ("<end>", ""),
}

VALID_TAGS = {"think", "execute", "results", "end"}


def parse_execute_block(xml_str: str) -> list[ToolCall]:
    xml_str = xml_str.strip()

    if "<execute>" not in xml_str or "</execute>" not in xml_str:
        raise ProtocolError("No <execute> block found", original_input=xml_str)

    try:
        start = xml_str.find("<execute>") + len("<execute>")
        end = xml_str.find("</execute>")
        content = xml_str[start:end].strip()

        calls_data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ProtocolError(f"Invalid JSON in <execute> block: {e}", original_input=xml_str) from e

    if not isinstance(calls_data, list):
        raise ProtocolError("Expected JSON array in <execute> block", original_input=xml_str)

    calls = []
    for i, call_obj in enumerate(calls_data):
        if not isinstance(call_obj, dict):
            raise ProtocolError(f"Call {i} is not an object: {call_obj}", original_input=xml_str)

        if "name" not in call_obj or "args" not in call_obj:
            raise ProtocolError(
                f"Call {i} missing 'name' or 'args': {call_obj}", original_input=xml_str
            )

        tool_name = call_obj["name"]
        args = call_obj["args"]

        if not isinstance(args, dict):
            raise ProtocolError(
                f"Call {i} args must be object, got {type(args).__name__}", original_input=xml_str
            )

        calls.append(ToolCall(name=tool_name, args=args))

    return calls


async def _wrap_string(text: str) -> AsyncGenerator[str, None]:
    yield text


def _find_next_tag(buffer: str) -> tuple[str, int, int] | None:
    earliest_pos = len(buffer)
    earliest_tag = None

    for tag_name in VALID_TAGS:
        open_tag = TAG_PATTERN[tag_name][0]
        pos = buffer.find(open_tag)
        if pos != -1 and pos < earliest_pos:
            earliest_pos = pos
            earliest_tag = tag_name

    if earliest_tag is None:
        return None

    open_tag = TAG_PATTERN[earliest_tag][0]
    return earliest_tag, earliest_pos, earliest_pos + len(open_tag)


def _find_closing_tag(buffer: str, tag_name: str) -> int | None:
    close_tag = TAG_PATTERN[tag_name][1]
    pos = buffer.find(close_tag)
    if pos == -1:
        return None
    return pos + len(close_tag)


async def _emit_tool_calls_from_execute(xml_block: str) -> AsyncGenerator[Event, None]:
    tool_calls = parse_execute_block(xml_block)
    for call in tool_calls:
        call_json = json.dumps({"name": call.name, "args": call.args})
        yield {"type": "call", "content": call_json, "timestamp": time.time()}


async def parse_tokens(  # noqa: C901  # streaming XML tag parser state machine
    token_stream: AsyncGenerator[str, None] | str,
) -> AsyncGenerator[Event, None]:
    if isinstance(token_stream, str):
        token_stream = _wrap_string(token_stream)

    buffer = ""

    async for token in token_stream:
        if not isinstance(token, str):
            raise RuntimeError(f"Parser expects string tokens, got {type(token)}")

        logger.debug(f"TOKEN: {token!r}")
        buffer += token

        while True:
            tag_info = _find_next_tag(buffer)
            if not tag_info:
                break

            tag_name, start_pos, open_end = tag_info
            close_pos = _find_closing_tag(buffer[open_end:], tag_name)

            if close_pos is None:
                break

            close_pos += open_end

            prefix = buffer[:start_pos]
            if prefix.strip():
                yield {"type": "respond", "content": prefix, "timestamp": time.time()}

            content_start = open_end
            content_end = close_pos - len(TAG_PATTERN[tag_name][1])
            content = buffer[content_start:content_end]

            if tag_name == "execute":
                try:
                    async for event in _emit_tool_calls_from_execute(
                        f"<execute>{content}</execute>"
                    ):
                        yield event
                    yield {"type": "execute", "timestamp": time.time()}
                    return
                except ProtocolError as e:
                    logger.error(f"Malformed <execute> block: {e}")
                    yield {
                        "type": "respond",
                        "content": f"Error: Malformed tool call syntax. {e}",
                        "timestamp": time.time(),
                    }
            elif tag_name == "think":
                if content.strip():
                    yield {"type": "think", "content": content, "timestamp": time.time()}
            elif tag_name == "results" and content.strip():
                yield {
                    "type": "result",
                    "content": content,
                    "timestamp": time.time(),
                    "payload": None,
                }
            elif tag_name == "end":
                yield {"type": "end", "timestamp": time.time()}

            buffer = buffer[close_pos:]

    if buffer:
        yield {"type": "respond", "content": buffer, "timestamp": time.time()}


__all__ = ["parse_tokens"]
