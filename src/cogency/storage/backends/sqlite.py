"""SQLite backend - CANONICAL Three-Horizon Split-State Model implementation."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import aiosqlite

if TYPE_CHECKING:
    from cogency.state.agent import UserProfile, Workspace

from .base import Store


class SQLite(Store):
    """CANONICAL SQLite backend implementing Three-Horizon Split-State Model per docs/dev/state.md"""

    def __init__(self, db_path: str = "cogency_state.db"):
        self.db_path = str(Path(db_path).expanduser().resolve())
        self.process_id = "default"

    async def _ensure_schema(self):
        """Create CANONICAL schema - matches docs/dev/state.md exactly."""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrency - ignore failures in tests
            try:
                await db.execute("PRAGMA journal_mode=WAL")
                await db.execute("PRAGMA synchronous=NORMAL")
                await db.execute("PRAGMA busy_timeout=30000")  # 30 second timeout for locks
            except Exception:
                # PRAGMA failures in tests/concurrent access are not critical
                pass

            # CANONICAL: Three-Horizon Split-State Model schema per docs/dev/state.md

            # Horizon 1: user_profiles table - permanent memory across sessions
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Horizon 2: task_workspaces table - task-scoped memory for continuation
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_workspaces (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    workspace_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            # Index for user workspace lookups and analytics
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_workspace_user ON task_workspaces(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_workspace_updated ON task_workspaces(updated_at)"
            )

            # Remove legacy agent_states table (migration to canonical model)
            await db.execute("DROP TABLE IF EXISTS agent_states")

            await db.commit()

    # CANONICAL: Horizon 1 Operations (UserProfile)

    async def save_user_profile(self, state_key: str, profile: "UserProfile") -> bool:
        """CANONICAL: Save Horizon 1 - UserProfile to user_profiles table"""
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

    async def load_user_profile(self, state_key: str) -> Optional["UserProfile"]:
        """CANONICAL: Load Horizon 1 - UserProfile from user_profiles table"""
        await self._ensure_schema()

        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.state.agent import UserProfile

            user_id = state_key.split(":")[0]

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT profile_data FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                profile_data = json.loads(row[0])

                # Reconstruct UserProfile with datetime deserialization
                profile_kwargs = {}
                for field in fields(UserProfile):
                    if field.name in profile_data:
                        value = profile_data[field.name]
                        # Handle datetime deserialization
                        if field.name in ["created_at", "last_updated"] and isinstance(value, str):
                            value = datetime.fromisoformat(value)
                        profile_kwargs[field.name] = value

                return UserProfile(**profile_kwargs)

        except Exception:
            return None

    # CANONICAL: Horizon 2 Operations (Workspace)

    async def save_task_workspace(self, task_id: str, user_id: str, workspace: "Workspace") -> bool:
        """CANONICAL: Save Horizon 2 - Workspace to task_workspaces table by task_id"""
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
        """CANONICAL: Load Horizon 2 - Workspace from task_workspaces table by task_id"""
        await self._ensure_schema()

        try:
            from dataclasses import fields

            from cogency.state.agent import Workspace

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
        """CANONICAL: Delete Horizon 2 - Workspace on task completion"""
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

    # CANONICAL: Utility Operations

    async def delete_user_profile(self, state_key: str) -> bool:
        """CANONICAL: Delete user profile permanently"""
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
        """CANONICAL: List all task_ids for user's active workspaces"""
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

    # BASE CLASS COMPATIBILITY (Store interface)

    async def save(self, state_key: str, data: Union[Dict[str, Any], Any]) -> bool:
        """Store interface compatibility - serializes state data"""
        await self._ensure_schema()

        try:
            # Handle State objects
            if hasattr(data, "execution") and hasattr(data, "workspace"):
                # Full State object - serialize all components
                state_data = {
                    "state": {
                        "execution": {
                            "query": data.query,
                            "user_id": data.user_id,
                            "iteration": data.execution.iteration,
                            "mode": data.execution.mode,
                            "messages": data.execution.messages,
                            "stop_reason": data.execution.stop_reason,
                            "response": data.execution.response,
                            "pending_calls": data.execution.pending_calls,
                            "completed_calls": data.execution.completed_calls,
                            "iterations_without_tools": data.execution.iterations_without_tools,
                            "tool_results": data.execution.tool_results,
                        },
                        "reasoning": {
                            "objective": data.workspace.objective,
                            "assessment": data.workspace.assessment,
                            "approach": data.workspace.approach,
                            "observations": data.workspace.observations,
                            "insights": data.workspace.insights,
                            "facts": data.workspace.facts,
                            "thoughts": data.workspace.thoughts,
                        },
                        "user_profile": {
                            "user_id": data.profile.user_id,
                            "preferences": data.profile.preferences,
                            "goals": data.profile.goals,
                            "expertise_areas": data.profile.expertise_areas,
                            "communication_style": data.profile.communication_style,
                            "projects": data.profile.projects,
                            "interaction_count": getattr(data.profile, "interaction_count", 0),
                            "created_at": data.profile.created_at.isoformat(),
                            "last_updated": data.profile.last_updated.isoformat(),
                        }
                        if data.profile
                        else None,
                    }
                }
            else:
                # Raw data
                state_data = data if isinstance(data, dict) else {"state": data}

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS legacy_states (
                        state_key TEXT PRIMARY KEY,
                        state_data TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                await db.execute(
                    """
                    INSERT OR REPLACE INTO legacy_states (state_key, state_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (state_key, json.dumps(state_data)),
                )
                await db.commit()

            return True

        except Exception:
            return False

    async def load(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Store interface compatibility - deserializes state data"""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT state_data FROM legacy_states WHERE state_key = ?", (state_key,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                return json.loads(row[0])

        except Exception:
            return None

    async def delete(self, state_key: str) -> bool:
        """Store interface compatibility - deletes from legacy table"""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM legacy_states WHERE state_key = ?", (state_key,)
                )
                await db.commit()
                return cursor.rowcount > 0

        except Exception:
            return False

    async def list_states(self, user_id: str) -> List[str]:
        """Store interface compatibility - lists from legacy table"""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT state_key FROM legacy_states")
                rows = await cursor.fetchall()

                # Filter by user_id prefix - only return actual stored keys
                user_keys = [row[0] for row in rows if row[0].startswith(f"{user_id}:")]

                return user_keys

        except Exception:
            return []

    async def query_states(
        self, min_iteration: Optional[int] = None, mode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query states with filtering - compatibility for tests"""
        await self._ensure_schema()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT state_key, state_data FROM legacy_states")
                rows = await cursor.fetchall()

                results = []
                for state_key, state_data_json in rows:
                    try:
                        state_data = json.loads(state_data_json)

                        # Extract state info for filtering
                        execution = state_data.get("state", {}).get("execution", {})
                        iteration = execution.get("iteration", 0)
                        state_mode = execution.get("mode", "")
                        user_id = execution.get("user_id", "")

                        # Apply filters
                        if min_iteration is not None and iteration < min_iteration:
                            continue
                        if mode is not None and state_mode != mode:
                            continue

                        results.append(
                            {
                                "state_key": state_key,
                                "user_id": user_id,
                                "iteration": iteration,
                                "mode": state_mode,
                            }
                        )
                    except (json.JSONDecodeError, KeyError):
                        continue

                return results

        except Exception:
            return []
