"""Event persistence utilities."""

import json

from ..core.protocols import Event
from .resilience import resilient_save


def persister(conversation_id: str, user_id: str):
    """Create callback to save events to DB."""

    def save_event(event):
        event_type = event["type"]
        content = event.get("content", "")
        timestamp = event.get("timestamp")

        # Map event types to storage
        if event_type == Event.THINK:
            resilient_save(conversation_id, user_id, Event.THINK, content, timestamp)
        elif event_type == Event.CALLS:
            calls_content = json.dumps(event["calls"])
            resilient_save(conversation_id, user_id, Event.CALLS, calls_content, timestamp)
        elif event_type == Event.RESPOND:
            resilient_save(conversation_id, user_id, Event.RESPOND, content, timestamp)

    return save_event
