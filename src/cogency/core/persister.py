import time


class EventPersister:
    def __init__(self, conversation_id: str, user_id: str, storage):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.storage = storage

    async def persist(self, event_type: str, content: str, timestamp: float = None):
        if timestamp is None:
            timestamp = time.time()

        await self.storage.save_message(
            self.conversation_id, self.user_id, event_type, content, timestamp
        )
