import sqlite3
from pathlib import Path

from .display import Renderer


async def show_conversation(conversation_id: str):
    """Render conversation history using display renderer."""
    db_path = Path(".cogency/store.db")

    if not db_path.exists():
        print("No database found")
        return

    with sqlite3.connect(db_path) as db:
        rows = db.execute(
            "SELECT type, content FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()

    if not rows:
        print(f"No conversation found: {conversation_id}")
        return

    print(f"Conversation: {conversation_id}\n")

    async def replay_events():
        for msg_type, content in rows:
            yield {"type": msg_type, "content": content}

    renderer = Renderer()
    await renderer.render_stream(replay_events())
