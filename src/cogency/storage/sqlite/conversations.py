"""SQLite conversation operations - message history persistence."""

import json
from typing import TYPE_CHECKING, Optional

import aiosqlite

if TYPE_CHECKING:
    from cogency.state import Conversation

from .base import SQLiteBase
from ...events.orchestration import state_event, extract_conversation_data, extract_delete_data


class ConversationOperations(SQLiteBase):
    """SQLite operations for conversation persistence."""

    @state_event("conversation_saved", extract_conversation_data)
    async def save_conversation(self, conversation: "Conversation") -> bool:
        """Save conversation to storage."""
        await self._ensure_schema()

        try:
            from dataclasses import asdict

            conversation_dict = asdict(conversation)

            # Handle datetime serialization
            conversation_dict["last_updated"] = conversation.last_updated.isoformat()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO conversations (conversation_id, user_id, conversation_data, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        conversation.conversation_id,
                        conversation.user_id,
                        json.dumps(conversation_dict),
                    ),
                )
                await db.commit()

            return True

        except Exception:
            return False

    async def load_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional["Conversation"]:
        """Load conversation from storage."""
        await self._ensure_schema()

        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.state import Conversation

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT conversation_data FROM conversations WHERE conversation_id = ? AND user_id = ?",
                    (conversation_id, user_id),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                conversation_data = json.loads(row[0])

                # Reconstruct Conversation with datetime deserialization
                conversation_kwargs = {}
                for field in fields(Conversation):
                    if field.name in conversation_data:
                        value = conversation_data[field.name]
                        # Handle datetime deserialization
                        if field.name == "last_updated" and isinstance(value, str):
                            value = datetime.fromisoformat(value)
                        conversation_kwargs[field.name] = value

                return Conversation(**conversation_kwargs)

        except Exception:
            return None

    @state_event("conversation_deleted", extract_delete_data)
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation permanently."""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,)
                )
                await db.commit()
                return cursor.rowcount > 0

        except Exception:
            return False
