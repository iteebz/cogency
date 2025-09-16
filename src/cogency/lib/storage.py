"""SQLite storage with ACID properties for conversation persistence.

Operational characteristics:
- Auto-schema initialization per database path
- ACID transactions with retry logic for transient failures
- Async/sync bridging via thread executors
- Optimized indexes for conversation queries and profile lookups
- Thread-safe connection management
"""

import json
import sqlite3
import time
from pathlib import Path

from .paths import Paths
from .resilience import retry


class DB:
    _initialized_paths = set()

    @classmethod
    def connect(cls, base_dir: str = None):
        """Get database connection with schema initialization."""
        db_path = Paths.db(base_dir=base_dir)

        if str(db_path) not in cls._initialized_paths:
            cls._init_schema(db_path)
            cls._initialized_paths.add(str(db_path))

        return sqlite3.connect(db_path)

    @classmethod
    def _init_schema(cls, db_path: Path):
        """Initialize database schema."""
        with sqlite3.connect(db_path) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    PRIMARY KEY (conversation_id, timestamp)
                );

                CREATE INDEX IF NOT EXISTS idx_conversations_id ON conversations(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(type);
                CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
                CREATE INDEX IF NOT EXISTS idx_conversations_composite ON conversations(conversation_id, type, timestamp);
                CREATE INDEX IF NOT EXISTS idx_conversations_user_type ON conversations(user_id, type, timestamp);

                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    char_count INTEGER NOT NULL,
                    PRIMARY KEY (user_id, version)
                );

                CREATE INDEX IF NOT EXISTS idx_profiles_user_latest ON profiles(user_id, version DESC);
                CREATE INDEX IF NOT EXISTS idx_profiles_cleanup ON profiles(created_at);
            """)


class SQLite:
    """SQLite storage with retry logic and ACID guarantees."""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir

    @retry(attempts=3, base_delay=0.1)
    async def save_message(
        self, conversation_id: str, user_id: str, type: str, content: str, timestamp: float = None
    ) -> None:
        """Save message to conversation with retry logic."""
        import asyncio

        if timestamp is None:
            timestamp = time.time()

        def _sync_save():
            with DB.connect(self.base_dir) as db:
                db.execute(
                    "INSERT INTO conversations (conversation_id, user_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (conversation_id, user_id, type, content, timestamp),
                )

        await asyncio.get_event_loop().run_in_executor(None, _sync_save)

    async def load_messages(
        self, conversation_id: str, include: list[str] = None, exclude: list[str] = None
    ) -> list[dict]:
        """Load conversation messages with optional type filtering."""
        import asyncio

        def _sync_load():
            with DB.connect(self.base_dir) as db:
                db.row_factory = sqlite3.Row

                query = "SELECT type, content FROM conversations WHERE conversation_id = ?"
                params = [conversation_id]

                if include:
                    placeholders = ",".join("?" for _ in include)
                    query += f" AND type IN ({placeholders})"
                    params.extend(include)
                elif exclude:
                    placeholders = ",".join("?" for _ in exclude)
                    query += f" AND type NOT IN ({placeholders})"
                    params.extend(exclude)

                query += " ORDER BY timestamp"

                rows = db.execute(query, params).fetchall()
                return [{"type": row["type"], "content": row["content"]} for row in rows]

        return await asyncio.get_event_loop().run_in_executor(None, _sync_load)

    async def save_profile(self, user_id: str, profile: dict) -> None:
        """Save new user profile version. Raises on failure."""
        import asyncio

        def _sync_save():
            with DB.connect(self.base_dir) as db:
                current_version = (
                    db.execute(
                        "SELECT MAX(version) FROM profiles WHERE user_id = ?", (user_id,)
                    ).fetchone()[0]
                    or 0
                )

                next_version = current_version + 1
                profile_json = json.dumps(profile)
                char_count = len(profile_json)

                db.execute(
                    "INSERT INTO profiles (user_id, version, data, created_at, char_count) VALUES (?, ?, ?, ?, ?)",
                    (user_id, next_version, profile_json, time.time(), char_count),
                )

        await asyncio.get_event_loop().run_in_executor(None, _sync_save)

    async def load_profile(self, user_id: str) -> dict:
        """Load latest user profile."""
        import asyncio

        def _sync_load():
            with DB.connect(self.base_dir) as db:
                row = db.execute(
                    "SELECT data FROM profiles WHERE user_id = ? ORDER BY version DESC LIMIT 1",
                    (user_id,),
                ).fetchone()
                if row:
                    return json.loads(row[0])
                return {}

        return await asyncio.get_event_loop().run_in_executor(None, _sync_load)

    async def load_user_messages(
        self, user_id: str, since_timestamp: float = 0, limit: int | None = None
    ) -> list[str]:
        """Get user messages across all conversations for profile learning."""
        import asyncio

        def _sync_load():
            with DB.connect(self.base_dir) as db:
                query = "SELECT content FROM conversations WHERE user_id = ? AND type = 'user' AND timestamp > ? ORDER BY timestamp ASC"
                params = [user_id, since_timestamp]

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)

                rows = db.execute(query, params).fetchall()
                return [row[0] for row in rows]

        return await asyncio.get_event_loop().run_in_executor(None, _sync_load)

    async def count_user_messages(self, user_id: str, since_timestamp: float = 0) -> int:
        """Count user messages since timestamp for learning cadence."""
        import asyncio

        def _sync_count():
            with DB.connect(self.base_dir) as db:
                return db.execute(
                    "SELECT COUNT(*) FROM conversations WHERE user_id = ? AND type = 'user' AND timestamp > ?",
                    (user_id, since_timestamp),
                ).fetchone()[0]

        return await asyncio.get_event_loop().run_in_executor(None, _sync_count)


def clear_messages(conversation_id: str, base_dir: str = None) -> None:
    """Clear conversation for testing. Raises on failure."""
    with DB.connect(base_dir) as db:
        db.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))


def default_storage():
    return SQLite()
