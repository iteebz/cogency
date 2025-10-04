import json
import sqlite3
import time
from pathlib import Path

from .ids import uuid7
from .resilience import retry


class DB:
    _initialized_paths = set()

    @classmethod
    def connect(cls, db_path: str):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if str(path) not in cls._initialized_paths:
            cls._init_schema(path)
            cls._initialized_paths.add(str(path))

        return sqlite3.connect(path)

    @classmethod
    def _init_schema(cls, db_path: Path):
        with sqlite3.connect(db_path) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);
                CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
                CREATE INDEX IF NOT EXISTS idx_messages_user_type ON messages(user_id, type, timestamp);

                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_conversation ON events(conversation_id, timestamp);

                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT,
                    messages TEXT NOT NULL,
                    response TEXT,
                    timestamp REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_requests_conversation ON requests(conversation_id, timestamp);

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
    def __init__(self, db_path: str = ".cogency/store.db"):
        self.db_path = db_path

    @retry(attempts=3, base_delay=0.1)
    async def save_message(
        self, conversation_id: str, user_id: str, type: str, content: str, timestamp: float = None
    ) -> str:
        import asyncio

        if timestamp is None:
            timestamp = time.time()

        message_id = uuid7()

        def _sync_save():
            with DB.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO messages (message_id, conversation_id, user_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (message_id, conversation_id, user_id, type, content, timestamp),
                )

        await asyncio.get_event_loop().run_in_executor(None, _sync_save)
        return message_id

    @retry(attempts=3, base_delay=0.1)
    async def save_event(
        self, conversation_id: str, type: str, content: str, timestamp: float = None
    ) -> str:
        import asyncio

        if timestamp is None:
            timestamp = time.time()

        event_id = uuid7()

        def _sync_save():
            with DB.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO events (event_id, conversation_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (event_id, conversation_id, type, content, timestamp),
                )

        await asyncio.get_event_loop().run_in_executor(None, _sync_save)
        return event_id

    @retry(attempts=3, base_delay=0.1)
    async def save_request(
        self,
        conversation_id: str,
        user_id: str,
        messages: str,
        response: str = None,
        timestamp: float = None,
    ) -> str:
        import asyncio

        if timestamp is None:
            timestamp = time.time()

        request_id = uuid7()

        def _sync_save():
            with DB.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO requests (request_id, conversation_id, user_id, messages, response, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (request_id, conversation_id, user_id, messages, response, timestamp),
                )

        await asyncio.get_event_loop().run_in_executor(None, _sync_save)
        return request_id

    async def load_messages(
        self,
        conversation_id: str,
        user_id: str,
        include: list[str] = None,
        exclude: list[str] = None,
    ) -> list[dict]:
        import asyncio

        def _sync_load():
            with DB.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row

                query = "SELECT type, content FROM messages WHERE conversation_id = ?"
                params = [conversation_id]

                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)

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
        import asyncio

        def _sync_save():
            with DB.connect(self.db_path) as db:
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
        import asyncio

        def _sync_load():
            with DB.connect(self.db_path) as db:
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
        import asyncio

        def _sync_load():
            with DB.connect(self.db_path) as db:
                query = "SELECT content FROM messages WHERE user_id = ? AND type = 'user' AND timestamp > ? ORDER BY timestamp ASC"
                params = [user_id, since_timestamp]

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)

                rows = db.execute(query, params).fetchall()
                return [row[0] for row in rows]

        return await asyncio.get_event_loop().run_in_executor(None, _sync_load)

    async def count_user_messages(self, user_id: str, since_timestamp: float = 0) -> int:
        import asyncio

        def _sync_count():
            with DB.connect(self.db_path) as db:
                return db.execute(
                    "SELECT COUNT(*) FROM messages WHERE user_id = ? AND type = 'user' AND timestamp > ?",
                    (user_id, since_timestamp),
                ).fetchone()[0]

        return await asyncio.get_event_loop().run_in_executor(None, _sync_count)


def clear_messages(conversation_id: str, db_path: str = ".cogency/store.db") -> None:
    with DB.connect(db_path) as db:
        db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))


def default_storage(db_path: str = ".cogency/store.db"):
    return SQLite(db_path=db_path)
