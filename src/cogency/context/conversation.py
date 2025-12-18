import json
from typing import Any, cast


def _flush_assistant_turn(messages: list[dict[str, Any]], assistant_turn: list[str]) -> None:
    if assistant_turn:
        messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})


def _handle_result(
    messages: list[dict[str, Any]],
    assistant_turn: list[str],
    batch_calls: list[dict[str, Any]],
    event: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    if batch_calls:
        execute_xml = f"<execute>\n{json.dumps(batch_calls, indent=2)}\n</execute>"
        assistant_turn.append(execute_xml)
        _flush_assistant_turn(messages, assistant_turn)
        assistant_turn = []
        batch_calls = []

    content = event.get("content", "")
    if content:
        messages.append({"role": "user", "content": f"<results>\n{content}\n</results>"})

    return assistant_turn, batch_calls


def to_messages(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert event log to conversational messages with chronological reconstruction."""
    messages: list[dict[str, Any]] = []
    assistant_turn: list[str] = []
    batch_calls: list[dict[str, Any]] = []

    for event in events:
        t = event["type"]

        if t == "user":
            _flush_assistant_turn(messages, assistant_turn)
            assistant_turn = []
            batch_calls = []
            messages.append({"role": "user", "content": event["content"]})
        elif t == "think":
            assistant_turn.append(f"<think>{event['content']}</think>")
        elif t == "respond":
            assistant_turn.append(event["content"])
        elif t == "call":
            raw: object = json.loads(event["content"])
            if not isinstance(raw, dict):
                continue
            data = cast(dict[str, Any], raw)
            name = data.get("name")
            args = data.get("args")
            if isinstance(name, str) and isinstance(args, dict):
                batch_calls.append({"name": name, "args": cast(dict[str, Any], args)})
        elif t == "result":
            assistant_turn, batch_calls = _handle_result(
                messages, assistant_turn, batch_calls, event
            )

    _flush_assistant_turn(messages, assistant_turn)
    return messages
