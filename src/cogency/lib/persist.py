"""persistence utilities."""

import json

from .resilience import resilient_save


def persister(conversation_id: str, user_id: str):
    """Create callback to save events to DB."""

    def save_event(event):
        event_type = event["type"]
        content = event.get("content", "")
        timestamp = event.get("timestamp")

        # Map event types to storage
        if event_type == "think":
            resilient_save(conversation_id, user_id, "think", content, timestamp)
        elif event_type == "call":
            calls_content = json.dumps(event["calls"])
            resilient_save(conversation_id, user_id, "call", calls_content, timestamp)
        elif event_type == "respond":
            resilient_save(conversation_id, user_id, "respond", content, timestamp)

    return save_event
