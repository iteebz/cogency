"""SQLite backend for agent state storage."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import aiosqlite

if TYPE_CHECKING:
    from cogency.state import Conversation, Profile, Workspace

from . import StateStore


class SQLite(StateStore):
    """SQLite backend for agent state storage."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            cogency_dir = Path.home() / ".cogency"
            cogency_dir.mkdir(exist_ok=True)
            db_path = cogency_dir / "store.db"

        # Don't resolve :memory: paths - keep them as-is
        if db_path == ":memory:" or str(db_path).startswith(":memory:"):
            self.db_path = str(db_path)
        else:
            self.db_path = str(Path(db_path).expanduser().resolve())
        self.process_id = "default"

    async def _ensure_schema(self):
        """Create database schema for agent state storage."""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrency - ignore failures in tests
            try:
                await db.execute("PRAGMA journal_mode=WAL")
                await db.execute("PRAGMA synchronous=NORMAL")
                await db.execute("PRAGMA busy_timeout=30000")  # 30 second timeout for locks
            except Exception:
                # PRAGMA failures in tests/concurrent access are not critical
                pass

            # Agent state storage schema

            # User profiles table - permanent identity across sessions
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Conversations table - message history across tasks
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    conversation_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            # Task workspaces table - task-scoped context for continuation
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_workspaces (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    workspace_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            # Indexes for lookups and analytics
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_workspace_user ON task_workspaces(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_workspace_updated ON task_workspaces(updated_at)"
            )

            # Remove legacy agent_states table (migration to canonical model)
            await db.execute("DROP TABLE IF EXISTS agent_states")

            await db.commit()

    # Profile Operations

    async def save_user_profile(self, state_key: str, profile: "Profile") -> bool:
        """Save user profile to storage."""
        await self._ensure_schema()

        try:
            from dataclasses import asdict

            user_id = state_key.split(":")[0]
            profile_dict = asdict(profile)

            # Handle datetime serialization
            profile_dict["created_at"] = profile.created_at.isoformat()
            profile_dict["last_updated"] = profile.last_updated.isoformat()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles (user_id, profile_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, json.dumps(profile_dict)),
                )
                await db.commit()

            return True

        except Exception:
            return False

    async def load_user_profile(self, state_key: str) -> Optional["Profile"]:
        """Load user profile from storage."""
        await self._ensure_schema()

        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.state import Profile

            user_id = state_key.split(":")[0]

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT profile_data FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                profile_data = json.loads(row[0])

                # Reconstruct Profile with datetime deserialization
                profile_kwargs = {}
                for field in fields(Profile):
                    if field.name in profile_data:
                        value = profile_data[field.name]
                        # Handle datetime deserialization
                        if field.name in ["created_at", "last_updated"] and isinstance(value, str):
                            value = datetime.fromisoformat(value)
                        profile_kwargs[field.name] = value

                return Profile(**profile_kwargs)

        except Exception:
            return None

    # Conversation Operations

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

    # Workspace Operations

    async def save_task_workspace(self, task_id: str, user_id: str, workspace: "Workspace") -> bool:
        """Save task workspace to storage."""
        await self._ensure_schema()

        try:
            from dataclasses import asdict

            workspace_dict = asdict(workspace)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO task_workspaces (task_id, user_id, workspace_data, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (task_id, user_id, json.dumps(workspace_dict)),
                )
                await db.commit()

            return True

        except Exception:
            return False

    async def load_task_workspace(self, task_id: str, user_id: str) -> Optional["Workspace"]:
        """Load task workspace from storage."""
        await self._ensure_schema()

        try:
            from dataclasses import fields

            from cogency.state import Workspace

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT workspace_data FROM task_workspaces WHERE task_id = ? AND user_id = ?",
                    (task_id, user_id),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                workspace_data = json.loads(row[0])

                # Reconstruct Workspace
                workspace_kwargs = {}
                for field in fields(Workspace):
                    if field.name in workspace_data:
                        workspace_kwargs[field.name] = workspace_data[field.name]

                return Workspace(**workspace_kwargs)

        except Exception:
            return None

    async def delete_task_workspace(self, task_id: str) -> bool:
        """Delete task workspace on completion."""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM task_workspaces WHERE task_id = ?", (task_id,)
                )
                await db.commit()
                return cursor.rowcount > 0

        except Exception:
            return False

    # Utility Operations

    async def delete_user_profile(self, state_key: str) -> bool:
        """Delete user profile permanently."""
        await self._ensure_schema()

        try:
            user_id = state_key.split(":")[0]

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
                await db.commit()
                return cursor.rowcount > 0

        except Exception:
            return False

    async def list_user_workspaces(self, user_id: str) -> List[str]:
        """List all task_ids for user's active workspaces."""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT task_id FROM task_workspaces WHERE user_id = ?", (user_id,)
                )
                rows = await cursor.fetchall()

            return [row[0] for row in rows]
        except Exception:
            return []
