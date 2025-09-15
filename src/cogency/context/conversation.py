"""Canonical conversation context construction."""

import json

from ..core.protocols import Storage, ToolCall, ToolResult
from ..tools.format import format_call_agent, format_result_agent
from .constants import DEFAULT_CONVERSATION_ID


async def history(conversation_id: str, storage: Storage, history_window: int) -> str:
    """Past conversation excluding current cycle and think events."""
    if not conversation_id or conversation_id == DEFAULT_CONVERSATION_ID:
        return ""

    messages = await storage.load_messages(conversation_id)
    if not messages:
        return ""

    last_user = _last_user_index(messages)
    if last_user is None or last_user == 0:
        return ""

    # Filter think events and take last N efficiently - ONLY applies to history
    history_msgs = []
    for msg in reversed(messages[:last_user]):
        if msg["type"] != "think":
            history_msgs.append(msg)
            if len(history_msgs) >= history_window:
                break

    if not history_msgs:
        return ""

    return _format_section("HISTORY", list(reversed(history_msgs)))


async def current(conversation_id: str, storage: Storage) -> str:
    """Current cycle including think events - ALL current context included."""
    if not conversation_id or conversation_id == DEFAULT_CONVERSATION_ID:
        return ""

    messages = await storage.load_messages(conversation_id)
    if not messages:
        return ""

    last_user = _last_user_index(messages)
    if last_user is None:
        return ""

    current_msgs = messages[last_user:]
    return _format_section("CURRENT", current_msgs) if len(current_msgs) > 1 else ""


async def full_context(conversation_id: str, storage: Storage, history_window: int) -> str:
    """HISTORY + CURRENT sections."""
    h = await history(conversation_id, storage, history_window)
    c = await current(conversation_id, storage)

    if h and c:
        return f"{h}\n\n{c}"
    return c or h


def _last_user_index(messages: list[dict]) -> int | None:
    """Find index of last user message."""
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["type"] == "user":
            return i
    return None


def _format_section(name: str, messages: list[dict]) -> str:
    """Format section with header and protocol delimiters."""
    formatted = []

    for msg in messages:
        msg_type, content = msg["type"], msg["content"]

        if msg_type in ["user", "respond"] or (msg_type == "think" and name == "CURRENT"):
            formatted.extend([f"${msg_type}: {content}", ""])

        elif msg_type == "call":
            try:
                calls = json.loads(content) if content else []
                for call_data in calls:
                    call_obj = ToolCall(name=call_data["name"], args=call_data["args"])
                    formatted.extend([f"$call: {format_call_agent(call_obj)}", ""])
            except (json.JSONDecodeError, KeyError, TypeError):
                formatted.extend([f"$call: {content}", ""])

        elif msg_type == "result":
            try:
                results = json.loads(content) if content else []
                for result_data in results:
                    if isinstance(result_data, dict):
                        result_obj = ToolResult(
                            outcome=result_data.get("outcome", ""),
                            content=result_data.get("content", ""),
                        )
                    else:
                        result_obj = ToolResult(outcome=str(result_data), content="")
                    formatted.extend([f"$result: {format_result_agent(result_obj)}", ""])
            except (json.JSONDecodeError, KeyError, TypeError):
                formatted.extend([f"$result: {content}", ""])

    return f"=== {name} ===\n\n" + "\n".join(formatted)
