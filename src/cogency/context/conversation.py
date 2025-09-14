"""Conversation history construction for context assembly."""

import json

from ..lib.storage import load_messages
from .constants import DEFAULT_CONVERSATION_ID, HISTORY_LIMIT


async def history(conversation_id: str) -> str:
    """Context assembly algorithm:

    - Single system message with all context
    - History: Last N user/assistant/tools messages before current cycle
    - Format: USER:/ASSISTANT:/TOOLS: (reference markers)
    - Filtering: Skip 'think' events, truncate tool results
    - Prevents hallucination by excluding current cycle from history
    """
    if not conversation_id or conversation_id == DEFAULT_CONVERSATION_ID:
        return ""

    all_messages = await load_messages(conversation_id)
    if not all_messages:
        return ""

    # Find last user message to get cycle boundary
    last_user_idx = None
    for i in range(len(all_messages) - 1, -1, -1):
        if all_messages[i]["type"] == "user":
            last_user_idx = i
            break

    if last_user_idx is None or last_user_idx == 0:
        return ""  # No history or only current message

    # Get past messages (before current cycle) and filter out 'think'
    past_messages = all_messages[:last_user_idx]
    conversational_messages = [msg for msg in past_messages if msg["type"] != "think"]
    if not conversational_messages:
        return ""

    # Take last N conversational messages (user/assistant/tools only)
    history_messages = conversational_messages[-HISTORY_LIMIT:]

    # Format messages with call/result pairing
    formatted = []
    i = 0
    while i < len(history_messages):
        msg = history_messages[i]
        msg_type = msg["type"]
        content = msg["content"]

        if msg_type == "call":
            calls = json.loads(content) if content else []
            results = []

            # Grab matching results from next message
            if i + 1 < len(history_messages) and history_messages[i + 1]["type"] == "result":
                results_content = history_messages[i + 1]["content"]
                results = json.loads(results_content) if results_content else []
                i += 1  # Skip results message

            # Pair calls with results
            if calls:
                pairs = []
                for j, call in enumerate(calls):
                    result = results[j] if j < len(results) else "No result"
                    pairs.append({"call": call, "result": result})

                from ..lib.format import format_tools

                tools_display = format_tools(json.dumps(pairs), truncate=True)
                formatted.append(f"TOOLS: {tools_display}")

        elif msg_type == "result":
            pass  # Skip standalone results
        elif msg_type == "respond":
            formatted.append(f"ASSISTANT: {content}")
        else:
            formatted.append(f"{msg_type.upper()}: {content}")

        i += 1

    return "\n".join(formatted) if formatted else ""


async def current_cycle_messages(conversation_id: str) -> list[dict]:
    """Get current cycle messages for replay mode continuity.

    Current cycle reconstruction:
    - Everything after last user message
    - Format as assistant/system conversation messages
    - Enables multi-iteration cycle memory
    """
    if not conversation_id or conversation_id == DEFAULT_CONVERSATION_ID:
        return []

    all_messages = await load_messages(conversation_id)
    if not all_messages:
        return []

    # Find last user message to get current cycle boundary
    last_user_idx = None
    for i in range(len(all_messages) - 1, -1, -1):
        if all_messages[i]["type"] == "user":
            last_user_idx = i
            break

    if last_user_idx is None or last_user_idx == len(all_messages) - 1:
        return []  # No current cycle or user message is last

    # Get current cycle messages (after last user message)
    current_cycle = all_messages[last_user_idx + 1 :]
    if not current_cycle:
        return []

    # Format current cycle into natural conversation
    lines = []
    for record in current_cycle:
        msg_type = record["type"]
        content = record["content"]

        if msg_type == "think":
            lines.append(f"Thinking: {content}")
        elif msg_type == "call":
            try:
                tools = json.loads(content) if content else []
                if tools:
                    tool_names = [tool.get("name", "unknown") for tool in tools]
                    lines.append(f"Used tools: {', '.join(tool_names)}")
            except json.JSONDecodeError:
                lines.append(f"Used tools: {content}")
        elif msg_type == "result":
            lines.append(f"Observed: {content}")
        elif msg_type == "respond":
            lines.append(f"Responded: {content}")

    natural_history = "\n".join(lines)
    if natural_history:
        return [{"role": "assistant", "content": f"Previous cycle:\n{natural_history}"}]
    return []
