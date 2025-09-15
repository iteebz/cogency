"""Event persistence - clean separation from stream processing."""

import time


class EventPersister:
    """Handles all conversation event persistence with uniform model."""

    def __init__(self, conversation_id: str, user_id: str, storage):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.storage = storage

    async def persist_event(self, event_type: str, content: str, timestamp: float = None):
        """Persist any event type uniformly."""
        if timestamp is None:
            timestamp = time.time()

        await self.storage.save_message(
            self.conversation_id, self.user_id, event_type, content, timestamp
        )
        # Let storage errors bubble up - don't hide them

    async def persist_think(self, content: str, timestamp: float = None):
        """Persist think event."""
        await self.persist_event("think", content, timestamp)

    async def persist_respond(self, content: str, timestamp: float = None):
        """Persist respond event."""
        await self.persist_event("respond", content, timestamp)

    async def persist_call(self, call_json: str, timestamp: float = None):
        """Persist tool call event."""
        await self.persist_event("call", call_json, timestamp)

    async def persist_result(self, result_content: str, timestamp: float = None):
        """Persist tool result event."""
        await self.persist_event("result", result_content, timestamp)
