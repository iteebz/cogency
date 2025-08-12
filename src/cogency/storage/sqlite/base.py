"""SQLite shared infrastructure - schema and connection management."""

from pathlib import Path

import aiosqlite

from cogency.config.paths import paths


class SQLiteBase:
    """Shared SQLite infrastructure for all domain operations."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            base_path = Path(paths.base_dir)
            base_path.mkdir(exist_ok=True)
            db_path = base_path / "store.db"

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

            # Knowledge vectors table - semantic memory for Recall tool
            await db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_vectors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    embedding TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_user ON knowledge_vectors(user_id)"
            )

            # Remove legacy agent_states table (migration to canonical model)
            await db.execute("DROP TABLE IF EXISTS agent_states")

            await db.commit()
