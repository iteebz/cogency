import asyncio
import json
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, TypeVar

from cogency.core.protocols import MessageMatch, parse_metric_data_dict, parse_profile_dict

from .resilience import retry
from .uuid7 import uuid7

DB_TIMEOUT_SECONDS = 5.0

T = TypeVar("T")


async def _run_sync(fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


class DB:
    _initialized_paths: ClassVar[dict[str, float]] = {}
    _CACHE_TTL: ClassVar[float] = 3600.0

    @classmethod
    def connect(cls, db_path: str):
        is_memory = db_path == ":memory:"

        if not is_memory:
            path = Path(db_path)
            path_str = str(path)
            now = time.time()

            cached_time = cls._initialized_paths.get(path_str)
            if cached_time is None or (now - cached_time) > cls._CACHE_TTL:
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.touch(exist_ok=True)
                cls._init_schema(path)
                cls._initialized_paths[path_str] = now

        conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT_SECONDS)

        if is_memory:
            cls._init_schema_memory(conn)
        else:
            for i in range(3):
                try:
                    conn.execute("PRAGMA journal_mode=WAL")
                    break
                except sqlite3.OperationalError:
                    if i == 2:
                        raise
                    time.sleep(0.1 * (i + 1))

        return conn

    @classmethod
    def _init_schema_memory(cls, conn: sqlite3.Connection):
        conn.executescript(cls._schema_sql())

    @classmethod
    def _init_schema(cls, db_path: Path):
        with sqlite3.connect(str(db_path)) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(cls._schema_sql())

    @staticmethod
    def _schema_sql() -> str:
        return """
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
        """


class SQLite:
    """SQLite storage. WAL mode, thread-safe (new connection per op)."""

    def __init__(self, db_path: str = ".cogency/store.db"):
        # Preserve :memory: as-is without path resolution
        if db_path == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = str(Path(db_path).resolve())

    @retry(attempts=3, base_delay=0.1)
    async def save_message(
        self,
        conversation_id: str,
        user_id: str,
        type: str,
        content: str,
        timestamp: float | None = None,
    ) -> str:
        if timestamp is None:
            timestamp = time.time()

        message_id = uuid7()

        def _sync_save() -> None:
            with DB.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO messages (message_id, conversation_id, user_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (message_id, conversation_id, user_id, type, content, timestamp),
                )

        await _run_sync(_sync_save)
        return message_id

    @retry(attempts=3, base_delay=0.1)
    async def save_event(
        self, conversation_id: str, type: str, content: str, timestamp: float | None = None
    ) -> str:
        if timestamp is None:
            timestamp = time.time()

        event_id = uuid7()

        def _sync_save() -> None:
            with DB.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO events (event_id, conversation_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (event_id, conversation_id, type, content, timestamp),
                )

        await _run_sync(_sync_save)
        return event_id

    @retry(attempts=3, base_delay=0.1)
    async def save_request(
        self,
        conversation_id: str,
        user_id: str,
        messages: str,
        response: str | None = None,
        timestamp: float | None = None,
    ) -> str:
        if timestamp is None:
            timestamp = time.time()

        event_id = uuid7()

        def _sync_save() -> None:
            content = json.dumps({"messages": messages, "response": response})
            with DB.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO events (event_id, conversation_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (event_id, conversation_id, "request", content, timestamp),
                )

        await _run_sync(_sync_save)
        return event_id

    @retry(attempts=3, base_delay=0.1)
    async def load_messages(
        self,
        conversation_id: str,
        user_id: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        def _sync_load() -> list[dict[str, Any]]:
            with DB.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row

                query = "SELECT type, content, timestamp FROM messages WHERE conversation_id = ?"
                params: list[Any] = [conversation_id]

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

                query += " ORDER BY timestamp DESC"

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)

                rows = db.execute(query, params).fetchall()
                return [
                    {"type": row["type"], "content": row["content"], "timestamp": row["timestamp"]}
                    for row in reversed(rows)
                ]

        return await _run_sync(_sync_load)

    async def save_profile(self, user_id: str, profile: dict[str, Any]) -> None:
        def _sync_save() -> None:
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

        await _run_sync(_sync_save)

    @retry(attempts=3, base_delay=0.1)
    async def load_profile(self, user_id: str) -> dict[str, Any]:
        def _sync_load() -> dict[str, Any]:
            with DB.connect(self.db_path) as db:
                row = db.execute(
                    "SELECT data FROM profiles WHERE user_id = ? ORDER BY version DESC LIMIT 1",
                    (user_id,),
                ).fetchone()
                if row:
                    raw: object = json.loads(row[0])
                    parsed = parse_profile_dict(raw)
                    return dict(parsed)
                return {}

        return await _run_sync(_sync_load)

    @retry(attempts=3, base_delay=0.1)
    async def load_user_messages(
        self, user_id: str, since_timestamp: float = 0, limit: int | None = None
    ) -> list[str]:
        def _sync_load() -> list[str]:
            with DB.connect(self.db_path) as db:
                query = "SELECT content FROM messages WHERE user_id = ? AND type = 'user' AND timestamp > ? ORDER BY timestamp ASC"
                params: list[Any] = [user_id, since_timestamp]

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)

                rows = db.execute(query, params).fetchall()
                return [row[0] for row in rows]

        return await _run_sync(_sync_load)

    @retry(attempts=3, base_delay=0.1)
    async def count_user_messages(self, user_id: str, since_timestamp: float = 0) -> int:
        def _sync_count() -> int:
            with DB.connect(self.db_path) as db:
                return db.execute(
                    "SELECT COUNT(*) FROM messages WHERE user_id = ? AND type = 'user' AND timestamp > ?",
                    (user_id, since_timestamp),
                ).fetchone()[0]

        return await _run_sync(_sync_count)

    @retry(attempts=3, base_delay=0.1)
    async def delete_profile(self, user_id: str) -> int:
        def _sync_delete() -> int:
            with DB.connect(self.db_path) as db:
                cursor = db.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
                return cursor.rowcount

        return await _run_sync(_sync_delete)

    @retry(attempts=3, base_delay=0.1)
    async def load_latest_metric(self, conversation_id: str) -> dict[str, Any] | None:
        def _sync_load() -> dict[str, Any] | None:
            with DB.connect(self.db_path) as db:
                row = db.execute(
                    "SELECT content FROM events WHERE conversation_id = ? AND type = 'metric' ORDER BY timestamp DESC LIMIT 1",
                    (conversation_id,),
                ).fetchone()
                if row and row[0]:
                    raw: object = json.loads(row[0])
                    parsed = parse_metric_data_dict(raw)
                    return dict(parsed)
                return None

        return await _run_sync(_sync_load)

    @retry(attempts=3, base_delay=0.1)
    async def load_messages_by_conversation_id(
        self, conversation_id: str, limit: int
    ) -> list[dict[str, Any]]:
        def _sync_load() -> list[dict[str, Any]]:
            with DB.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                rows = db.execute(
                    """
                    SELECT timestamp, content FROM messages
                    WHERE conversation_id = ? AND type = 'user'
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (conversation_id, limit),
                ).fetchall()
                return [{"timestamp": row["timestamp"], "content": row["content"]} for row in rows]

        return await _run_sync(_sync_load)

    @retry(attempts=3, base_delay=0.1)
    async def search_messages(
        self, query: str, user_id: str, exclude_conversation_id: str | None, limit: int = 3
    ) -> list[MessageMatch]:
        def _sync_search() -> list[MessageMatch]:
            with DB.connect(self.db_path) as db:
                keywords = query.lower().split()
                like_patterns = [f"%{keyword}%" for keyword in keywords]

                exclude_clause = ""
                params: list[str] = []

                if exclude_conversation_id:
                    exclude_clause = "AND conversation_id != ?"
                    params.append(exclude_conversation_id)

                like_clause = " OR ".join("LOWER(content) LIKE ?" for _ in like_patterns)
                params.extend(like_patterns)

                relevance_parts: list[str] = []
                score_params: list[str] = []
                for keyword in keywords:
                    relevance_parts.append(
                        "(LENGTH(content) - LENGTH(REPLACE(LOWER(content), ?, '')))"
                    )
                    score_params.append(keyword)

                relevance_score = " + ".join(relevance_parts)

                query_sql = f"""
                    SELECT content, timestamp, conversation_id,
                           ({relevance_score}) as relevance_score
                    FROM messages
                    WHERE type = 'user'
                    AND user_id = ?
                    {exclude_clause}
                    AND ({like_clause})
                    ORDER BY relevance_score DESC, timestamp DESC
                    LIMIT ?
                """
                final_params: list[str | int] = [*score_params, user_id, *params]
                final_params.append(limit)

                rows = db.execute(query_sql, final_params).fetchall()

                return [
                    MessageMatch(
                        content=row[0],
                        timestamp=row[1],
                        conversation_id=row[2],
                    )
                    for row in rows
                ]

        return await _run_sync(_sync_search)


def clear_messages(conversation_id: str, db_path: str = ".cogency/store.db") -> None:
    with DB.connect(db_path) as db:
        db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))


def default_storage(db_path: str = ".cogency/store.db") -> SQLite:
    return SQLite(db_path=db_path)
