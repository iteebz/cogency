import json

from ..core.protocols import ToolResult
from ..tools.format import format_result_agent


def to_messages(events: list[dict]) -> list[dict]:
    """Convert event log to conversational messages."""
    messages = []
    assistant_turn = []

    for i, event in enumerate(events):
        t = event["type"]

        if t == "user":
            if assistant_turn:
                messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})
                assistant_turn = []
            messages.append({"role": "user", "content": event["content"]})

        elif t in ["think", "respond"]:
            assistant_turn.append(f"§{t}: {event['content']}")

        elif t == "call":
            assistant_turn.append(f"§call: {event['content']}")
            if i + 1 < len(events) and events[i + 1]["type"] == "result":
                assistant_turn.append("§execute")
                messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})
                assistant_turn = []

        elif t == "result":
            content = event.get("content", "")
            try:
                result_dict = json.loads(content)
                result = ToolResult(
                    outcome=result_dict.get("outcome", ""),
                    content=result_dict.get("content", ""),
                )
                result_text = format_result_agent(result)
            except (json.JSONDecodeError, TypeError):
                result_text = content

            if result_text:
                messages.append({"role": "user", "content": f"{result_text}"})

    if assistant_turn:
        messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})

    return messages
