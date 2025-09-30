import json

from ..core.protocols import Storage, ToolCall, ToolResult
from ..tools.format import format_call_agent, format_result_agent
from ..tools.parse import parse_tool_result
from .constants import DEFAULT_CONVERSATION_ID


async def history(conversation_id: str, user_id: str, storage: Storage, history_window: int) -> str:
    if not conversation_id or conversation_id == DEFAULT_CONVERSATION_ID:
        return ""

    messages = await storage.load_messages(conversation_id, user_id)
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


async def current(conversation_id: str, user_id: str, storage: Storage) -> str:
    if not conversation_id or conversation_id == DEFAULT_CONVERSATION_ID:
        return ""

    messages = await storage.load_messages(conversation_id, user_id)
    if not messages:
        return ""

    last_user = _last_user_index(messages)
    if last_user is None:
        return ""

    current_msgs = messages[last_user:]
    return _format_section("CURRENT", current_msgs) if len(current_msgs) > 1 else ""


async def full_context(
    conversation_id: str, user_id: str, storage: Storage, history_window: int
) -> str:
    h = await history(conversation_id, user_id, storage, history_window)
    c = await current(conversation_id, user_id, storage)

    if h and c:
        return f"{h}\n\n{c}"
    return c or h


def _last_user_index(messages: list[dict]) -> int | None:
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["type"] == "user":
            return i
    return None


def _format_section(name: str, messages: list[dict]) -> str:
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
            payload = msg.get("payload")
            if isinstance(payload, dict):
                result_obj = ToolResult(
                    outcome=payload.get("outcome", ""),
                    content=payload.get("content", ""),
                )
                formatted.extend([f"$result: {format_result_agent(result_obj)}", ""])
            elif content:  # Fallback for old format
                results = parse_tool_result(content)
                for result_obj in results:
                    formatted.extend([f"$result: {format_result_agent(result_obj)}", ""])

    return f"=== {name} ===\n\n" + "\n".join(formatted)
