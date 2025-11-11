import json


def to_messages(events: list[dict]) -> list[dict]:
    """Convert event log to conversational messages with chronological reconstruction."""
    messages = []
    assistant_turn = []
    batch_calls = []

    for event in events:
        t = event["type"]

        if t == "user":
            if assistant_turn:
                messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})
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
            if batch_calls:
                execute_xml = f"<execute>\n{json.dumps(batch_calls, indent=2)}\n</execute>"
                assistant_turn.append(execute_xml)
                messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})
                assistant_turn = []
                batch_calls = []

            content = event.get("content", "")
            if content:
                results_xml = f"<results>\n{content}\n</results>"
                messages.append({"role": "user", "content": results_xml})

    if assistant_turn:
        messages.append({"role": "assistant", "content": "\n".join(assistant_turn)})

    return messages
