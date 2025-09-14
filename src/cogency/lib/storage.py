"""SQLite storage for conversation persistence."""

import json
import sqlite3
import time
from pathlib import Path

from .resilience import retry


def get_cogency_dir(base_dir: str = None) -> Path:
    """Get cogency directory, configurable like requests."""
    if base_dir:
        cogency_dir = Path(base_dir)
    else:
        cogency_dir = Path(".cogency")  # Local to current directory
    cogency_dir.mkdir(exist_ok=True)
    return cogency_dir


class Paths:
    """Clean path management for cogency directories."""

    @staticmethod
    def db(subpath: str = None, base_dir: str = None) -> Path:
        """Get database path with optional subpath."""
        base = get_cogency_dir(base_dir) / "store.db"
        return base / subpath if subpath else base

    @staticmethod
    def sandbox(subpath: str = None, base_dir: str = None) -> Path:
        """Get sandbox path with optional subpath."""
        base = get_cogency_dir(base_dir) / "sandbox"
        base.mkdir(exist_ok=True)
        return base / subpath if subpath else base

    @staticmethod
    def evals(subpath: str = None, base_dir: str = None) -> Path:
        """Get evaluations path with optional subpath."""
        base = get_cogency_dir(base_dir) / "evals"
        base.mkdir(exist_ok=True)
        return base / subpath if subpath else base


class DB:
    _initialized_paths = set()

    @classmethod
    def connect(cls, base_dir: str = None):
        """Get database connection with automatic initialization."""
        db_path = Paths.db(base_dir=base_dir)

        if str(db_path) not in cls._initialized_paths:
            cls._init_schema(db_path)
            cls._initialized_paths.add(str(db_path))

        return sqlite3.connect(db_path)

    @classmethod
    def _init_schema(cls, db_path: Path):
        """Initialize database schema once."""
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


def _filter_type(include: list[str] = None, exclude: list[str] = None):
    """Filter message types - return SQL clause and params."""
    if include:
        placeholders = ",".join("?" for _ in include)
        return f" AND type IN ({placeholders})", include
    if exclude:
        placeholders = ",".join("?" for _ in exclude)
        return f" AND type NOT IN ({placeholders})", exclude
    return "", []


async def load_messages(
    conversation_id: str, base_dir: str = None, include: list[str] = None, exclude: list[str] = None
) -> list[dict]:
    """Load conversation from SQLite with optional type filtering."""
    import asyncio

    def _sync_load():
        with DB.connect(base_dir) as db:
            db.row_factory = sqlite3.Row

            # Base query with filter
            query = "SELECT type, content FROM conversations WHERE conversation_id = ?"
            params = [conversation_id]

            filter_clause, filter_params = _filter_type(include, exclude)
            query += filter_clause
            params.extend(filter_params)

            query += " ORDER BY timestamp"

            rows = db.execute(query, params).fetchall()
            return [{"type": row["type"], "content": row["content"]} for row in rows]

    return await asyncio.get_event_loop().run_in_executor(None, _sync_load)


@retry(attempts=3, base_delay=0.1)
async def save_message(
    conversation_id: str,
    user_id: str,
    type: str,
    content: str,
    base_dir: str = None,
    timestamp: float = None,
) -> None:
    """Save single message to conversation - O(1) operation with retry. Raises on failure."""
    import asyncio

    if timestamp is None:
        timestamp = time.time()

    def _sync_save():
        with DB.connect(base_dir) as db:
            db.execute(
                "INSERT INTO conversations (conversation_id, user_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, user_id, type, content, timestamp),
            )

    # Run sync SQLite operation in thread pool for protocol compliance
    await asyncio.get_event_loop().run_in_executor(None, _sync_save)


async def load_profile(user_id: str, base_dir: str = None) -> dict:
    """Load latest user profile from SQLite."""
    import asyncio

    def _sync_load():
        with DB.connect(base_dir) as db:
            row = db.execute(
                "SELECT data FROM profiles WHERE user_id = ? ORDER BY version DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if row:
                return json.loads(row[0])
            return {}

    return await asyncio.get_event_loop().run_in_executor(None, _sync_load)


async def save_profile(user_id: str, profile: dict, base_dir: str = None) -> None:
    """Save new user profile version to SQLite. Raises on failure."""
    import asyncio

    def _sync_save():
        with DB.connect(base_dir) as db:
            # Get next version atomically
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


class SQLite:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir

    async def save_message(
        self, conversation_id: str, user_id: str, type: str, content: str, timestamp: float = None
    ) -> None:
        await save_message(conversation_id, user_id, type, content, self.base_dir, timestamp)

    async def load_messages(
        self, conversation_id: str, include: list[str] = None, exclude: list[str] = None
    ) -> list[dict]:
        return await load_messages(conversation_id, self.base_dir, include, exclude)

    async def save_profile(self, user_id: str, profile: dict) -> None:
        await save_profile(user_id, profile, self.base_dir)

    async def load_profile(self, user_id: str) -> dict:
        return await load_profile(user_id, self.base_dir)

    async def record_message(self, conversation_id: str, user_id: str, events: list) -> None:
        """Record batch of events using agent's configured storage. Raises on failure."""
        import json

        for event in events:
            timestamp = event.get("timestamp")
            content = event.get("content", "")
            event_type = event["type"]

            # Serialize complex event content (same logic as context.record)
            if event_type == "call":
                content = json.dumps(event["calls"])
            elif event_type == "result":
                content = json.dumps(event["results"])

            # Convert enum to string for storage
            type_str = event_type.value if hasattr(event_type, "value") else event_type

            await self.save_message(conversation_id, user_id, type_str, content, timestamp)


def clear_messages(conversation_id: str, base_dir: str = None) -> None:
    """Clear conversation for testing. Raises on failure."""
    with DB.connect(base_dir) as db:
        db.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))


def default_storage():
    return SQLite()
