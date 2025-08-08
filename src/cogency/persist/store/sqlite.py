"""SQLite persistence store - persistent-first state management with atomic operations."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiosqlite

from cogency.persist.serialize import serialize_dataclass, serialize_profile
from cogency.state import AgentState

from .base import Store


class SQLiteStore(Store):
    """SQLite-based state persistence with JSON blobs and queryable metadata."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite store.

        Args:
            db_path: Database file path. If None, uses default from config.
                    Use ":memory:" for in-memory database.
        """
        from ...config import PathsConfig

        if db_path is None:
            paths = PathsConfig()
            self.db_path = Path(paths.base_dir) / "store.db"
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = db_path

    async def _ensure_schema(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrency
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")

            # Canonical schema: 3 columns only
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_states (
                    user_id TEXT PRIMARY KEY,
                    state_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for analytics queries
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_updated_at ON agent_states(updated_at)"
            )

            # Memory profiles table (separate for cleaner organization)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def save(self, state_key: str, state: Union[AgentState, Dict[str, Any]]) -> bool:
        """Save state with atomic transaction."""
        await self._ensure_schema()

        try:
            # Handle profile keys separately
            if state_key.startswith("profile:"):
                return await self._save_profile(state_key, state)

            # Handle AgentState
            if isinstance(state, AgentState):
                state_data = {
                    "execution": serialize_dataclass(state.execution),
                    "reasoning": serialize_dataclass(state.reasoning),
                    "user_profile": serialize_profile(state.user) if state.user else None,
                }
            else:
                # Raw dict (backward compatibility)
                state_data = state

            # Extract user_id from state_key (format: "user_id:process_id")
            user_id = state_key.split(":")[0]

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO agent_states (user_id, state_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (user_id, json.dumps(state_data)),
                )
                await db.commit()

            return True

        except Exception:
            return False

    async def _save_profile(self, state_key: str, profile_data: Dict[str, Any]) -> bool:
        """Save user profile separately."""
        try:
            user_id = state_key.replace("profile:", "")

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles (user_id, profile_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        user_id,
                        json.dumps(profile_data.get("state", profile_data)),
                    ),
                )
                await db.commit()

            return True
        except Exception:
            return False

    async def load(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load state from database."""
        await self._ensure_schema()

        try:
            # Handle profile keys
            if state_key.startswith("profile:"):
                return await self._load_profile(state_key)

            user_id = state_key.split(":")[0]

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT state_data FROM agent_states WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()

                if row:
                    return {"state": json.loads(row[0])}
                return None

        except Exception:
            return None

    async def _load_profile(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load user profile."""
        try:
            user_id = state_key.replace("profile:", "")

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT profile_data FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()

                if row:
                    return {"state": json.loads(row[0])}
                return None

        except Exception:
            return None

    async def delete(self, state_key: str) -> bool:
        """Delete state from database."""
        await self._ensure_schema()

        try:
            if state_key.startswith("profile:"):
                user_id = state_key.replace("profile:", "")
                table = "user_profiles"
            else:
                user_id = state_key.split(":")[0]
                table = "agent_states"

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
                await db.commit()

            return True
        except Exception:
            return False

    async def list_states(self, user_id: str) -> List[str]:
        """List all state keys for a user."""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT user_id FROM agent_states WHERE user_id LIKE ?", (f"{user_id}%",)
                )
                rows = await cursor.fetchall()

                # Return state keys in original format
                return [f"{row[0]}:default" for row in rows]

        except Exception:
            return []

    async def query_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query all states for analytics."""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT user_id, state_data, updated_at
                    FROM agent_states 
                    ORDER BY updated_at DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                rows = await cursor.fetchall()

                return [
                    {
                        "user_id": row[0],
                        "state_data": json.loads(row[1]),
                        "updated_at": row[2],
                    }
                    for row in rows
                ]

        except Exception:
            return []
