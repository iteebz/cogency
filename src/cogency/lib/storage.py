"""Storage: Canonical SQLite backend for persistence."""

import json
import sqlite3
import time
from pathlib import Path


def get_cogency_dir(base_dir: str = None) -> Path:
    """Get cogency directory, configurable like requests."""
    if base_dir:
        cogency_dir = Path(base_dir)
    else:
        cogency_dir = Path.home() / ".cogency"
    cogency_dir.mkdir(exist_ok=True)
    return cogency_dir


def get_db_path(base_dir: str = None) -> Path:
    """Get SQLite database path."""
    return get_cogency_dir(base_dir) / "cogency.db"


def _init_db(db_path: Path):
    """Initialize database schema - canonical tables only."""
    with sqlite3.connect(db_path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                PRIMARY KEY (conversation_id, timestamp)
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_id ON conversations(conversation_id);

            CREATE TABLE IF NOT EXISTS memory (
                user_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
        """)


def load_conversations(conversation_id: str, base_dir: str = None) -> list[dict]:
    """Load single conversation from SQLite."""
    db_path = get_db_path(base_dir)
    _init_db(db_path)

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT role, content FROM conversations WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()

        return [{"role": row["role"], "content": row["content"]} for row in rows]


def save_conversation_message(
    conversation_id: str, role: str, content: str, base_dir: str = None
) -> bool:
    """Save single message to conversation - O(1) operation."""
    db_path = get_db_path(base_dir)
    _init_db(db_path)

    try:
        with sqlite3.connect(db_path) as db:
            db.execute(
                "INSERT INTO conversations (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, time.time()),
            )
        return True
    except Exception:
        return False


def load_memory(user_id: str, base_dir: str = None) -> dict:
    """Load user memory from SQLite."""
    db_path = get_db_path(base_dir)
    _init_db(db_path)

    with sqlite3.connect(db_path) as db:
        row = db.execute("SELECT data FROM memory WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return json.loads(row[0])
        return {}


def save_memory(user_id: str, memory: dict, base_dir: str = None) -> bool:
    """Save user memory to SQLite."""
    db_path = get_db_path(base_dir)
    _init_db(db_path)

    try:
        with sqlite3.connect(db_path) as db:
            db.execute(
                "INSERT OR REPLACE INTO memory (user_id, data, updated_at) VALUES (?, ?, ?)",
                (user_id, json.dumps(memory), time.time()),
            )
        return True
    except Exception:
        return False
