"""Event persistence utilities."""

import json

from ..core.protocols import Event
from .resilience import resilient_save


def create_event_persister(conversation_id: str, user_id: str):
    """Create immediate DB write callback for semantic events.

    Features:
    - Event-aware translation to storage format
    - Retry logic with debug logging on failure
    - Clean separation from execution modes
    """

    def persist_event(event):
        """Persist semantic event immediately to database."""
        event_type = event["type"]
        content = event.get("content", "")
        timestamp = event.get("timestamp")

        # Map event types to storage types with resilience
        if event_type == Event.THINK:
            resilient_save(conversation_id, user_id, Event.THINK, content, timestamp)
        elif event_type == Event.CALLS:
            # Serialize calls for storage
            calls_content = json.dumps(event["calls"])
            resilient_save(conversation_id, user_id, Event.CALLS, calls_content, timestamp)
        elif event_type == Event.RESPOND:
            resilient_save(conversation_id, user_id, Event.RESPOND, content, timestamp)
        else:
            # Unknown event type - skip persistence
            return

    return persist_event
