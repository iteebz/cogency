"""SQLite workspace operations - task-scoped state persistence."""

import json
from typing import TYPE_CHECKING, Optional

import aiosqlite

if TYPE_CHECKING:
    from cogency.state import Workspace

from .base import SQLiteBase


class WorkspaceOperations(SQLiteBase):
    """SQLite operations for workspace persistence."""

    async def save_workspace(self, task_id: str, user_id: str, workspace: "Workspace") -> bool:
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

    async def load_workspace(self, task_id: str, user_id: str) -> Optional["Workspace"]:
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

    async def clear_workspace(self, task_id: str) -> bool:
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

    async def list_workspaces(self, user_id: str) -> list[str]:
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
