"""SQLite conversation operations - primitive data persistence."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

from ...events.orchestration import domain_event, extract_conversation_data, extract_delete_data


async def _ensure_schema(db_path: str):
    """Ensure conversation schema exists."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)"
        )
        await db.commit()


def _get_db_path(db_path: str = None) -> str:
    """Get database path with defaults."""
    if db_path is None:
        from cogency.config.paths import paths

        base_path = Path(paths.base_dir)
        base_path.mkdir(exist_ok=True)
        db_path = base_path / "store.db"

    if db_path == ":memory:" or str(db_path).startswith(":memory:"):
        return str(db_path)
    return str(Path(db_path).expanduser().resolve())


@domain_event("conversation_saved", extract_conversation_data)
async def save_conversation_data(
    conversation_id: str,
    user_id: str,
    messages: list[dict],
    last_updated: datetime = None,
    db_path: str = None,
) -> bool:
    """Save conversation data to storage - primitive data operation."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        if last_updated is None:
            last_updated = datetime.now()

        conversation_dict = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "messages": messages,
            "last_updated": last_updated.isoformat(),
        }

        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO conversations (conversation_id, user_id, conversation_data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (conversation_id, user_id, json.dumps(conversation_dict)),
            )
            await db.commit()

        return True

    except Exception:
        return False


async def load_conversation_data(
    conversation_id: str, user_id: str, db_path: str = None
) -> Optional[dict]:
    """Load conversation data from storage - primitive data operation."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT conversation_data FROM conversations WHERE conversation_id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
            row = await cursor.fetchone()

            if not row:
                return None

            conversation_data = json.loads(row[0])

            # Handle datetime deserialization
            if "last_updated" in conversation_data and isinstance(
                conversation_data["last_updated"], str
            ):
                conversation_data["last_updated"] = datetime.fromisoformat(
                    conversation_data["last_updated"]
                )

            return conversation_data

    except Exception:
        return None


async def save_conversation(conversation, db_path: str = None) -> bool:
    """Save conversation to storage - canonical domain object operation."""
    return await save_conversation_data(
        conversation.conversation_id,
        conversation.user_id,
        conversation.messages,
        conversation.last_updated,
        db_path,
    )


async def load_conversation(conversation_id: str, user_id: str, db_path: str = None):
    """Load conversation from storage - canonical domain object operation."""
    data = await load_conversation_data(conversation_id, user_id, db_path)
    if not data:
        return None

    # Import here to avoid circular dependency
    from cogency.context.conversation import Conversation

    return Conversation(
        conversation_id=data["conversation_id"],
        user_id=data["user_id"],
        messages=data["messages"],
        last_updated=data["last_updated"],
    )


async def create_conversation(user_id: str, db_path: str = None):
    """Create new conversation."""
    from cogency.context.conversation import Conversation

    conversation = Conversation(user_id=user_id)
    await save_conversation(conversation, db_path)
    return conversation


@domain_event("conversation_deleted", extract_delete_data)
async def delete_conversation(conversation_id: str, db_path: str = None) -> bool:
    """Delete conversation permanently."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    except Exception:
        return False


async def list_conversations(
    user_id: str, limit: int = 50, db_path: str = None
) -> list[dict[str, str]]:
    """List conversations for user with metadata - canonical conversation management."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
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
                title = _extract_conversation_title(data)

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


def _extract_conversation_title(conversation_data: dict) -> str:
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
