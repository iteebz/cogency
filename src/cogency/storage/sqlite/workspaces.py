"""SQLite workspace operations - primitive task-scoped data persistence."""

import json
from pathlib import Path
from typing import Optional

import aiosqlite

from ...events.orchestration import domain_event, extract_delete_data, extract_workspace_data


async def _ensure_schema(db_path: str):
    """Ensure workspace schema exists."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_workspaces (
                task_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                workspace_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_workspace_user ON task_workspaces(user_id)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_workspace_updated ON task_workspaces(updated_at)"
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


@domain_event("workspace_saved", extract_workspace_data)
async def save_workspace_data(
    task_id: str, user_id: str, workspace_data: dict, db_path: str = None
) -> bool:
    """Save task workspace to storage."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO task_workspaces (task_id, user_id, workspace_data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (task_id, user_id, json.dumps(workspace_data)),
            )
            await db.commit()

        return True

    except Exception:
        return False


async def load_workspace_data(task_id: str, user_id: str, db_path: str = None) -> Optional[dict]:
    """Load task workspace data from storage - primitive data operation."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT workspace_data FROM task_workspaces WHERE task_id = ? AND user_id = ?",
                (task_id, user_id),
            )
            row = await cursor.fetchone()

            if not row:
                return None

            return json.loads(row[0])

    except Exception:
        return None


@domain_event("workspace_deleted", extract_delete_data)
async def clear_workspace(task_id: str, db_path: str = None) -> bool:
    """Delete task workspace on completion."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("DELETE FROM task_workspaces WHERE task_id = ?", (task_id,))
            await db.commit()
            return cursor.rowcount > 0

    except Exception:
        return False


async def list_workspaces(user_id: str, db_path: str = None) -> list[str]:
    """List all task_ids for user's active workspaces."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT task_id FROM task_workspaces WHERE user_id = ?", (user_id,)
            )
            rows = await cursor.fetchall()

        return [row[0] for row in rows]
    except Exception:
        return []
