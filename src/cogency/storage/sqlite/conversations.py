"""SQLite conversation operations - message history persistence."""

import json
from typing import TYPE_CHECKING, Optional

import aiosqlite

if TYPE_CHECKING:
    from cogency.state import Conversation

from ...events.orchestration import extract_conversation_data, extract_delete_data, state_event
from .base import SQLiteBase


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

    async def list_conversations(self, user_id: str, limit: int = 50) -> list[dict[str, str]]:
        """List conversations for user with metadata - canonical conversation management."""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT conversation_id, conversation_data, updated_at
                    FROM conversations
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
                rows = await cursor.fetchall()

                conversations = []
                for row in rows:
                    conversation_id, conversation_data, updated_at = row

                    # Extract title from conversation data
                    data = json.loads(conversation_data)
                    title = self._extract_conversation_title(data)

                    conversations.append(
                        {
                            "conversation_id": conversation_id,
                            "title": title,
                            "updated_at": updated_at,
                            "message_count": len(data.get("messages", [])),
                        }
                    )

                return conversations

        except Exception:
            return []

    def _extract_conversation_title(self, conversation_data: dict) -> str:
        """Extract meaningful title from conversation data."""
        messages = conversation_data.get("messages", [])
        if not messages:
            return "Empty conversation"

        # Get first user message for title
        first_user_msg = None
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content"):
                first_user_msg = msg["content"]
                break

        if not first_user_msg:
            return "No user messages"

        # Create title from first message
        title = first_user_msg.strip()
        if len(title) > 60:
            title = title[:57] + "..."

        return title
