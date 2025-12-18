import json


def _flush_assistant_turn(messages: list[dict], assistant_turn: list[str]) -> None:
    if assistant_turn:
        messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})


def _handle_result(
    messages: list[dict], assistant_turn: list[str], batch_calls: list[dict], event: dict
) -> tuple[list[str], list[dict]]:
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


def to_messages(events: list[dict]) -> list[dict]:
    """Convert event log to conversational messages with chronological reconstruction."""
    messages = []
    assistant_turn = []
    batch_calls = []

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
            call_data = json.loads(event["content"])
            batch_calls.append({"name": call_data["name"], "args": call_data["args"]})
        elif t == "result":
            assistant_turn, batch_calls = _handle_result(
                messages, assistant_turn, batch_calls, event
            )

    _flush_assistant_turn(messages, assistant_turn)
    return messages
