"""State persistence manager - CANONICAL Three-Horizon Split-State Model."""

from typing import Optional

from cogency.events import emit
from cogency.state import State
from cogency.state.agent import UserProfile, Workspace
from cogency.storage.backends import SQLite, Store


class Persistence:
    """CANONICAL: Manages persistence for Three-Horizon Split-State Model per docs/dev/state.md"""

    def __init__(self, store: Optional[Store] = None, enabled: bool = True):
        self.store = store or SQLite()
        self.enabled = enabled

    def _state_key(self, user_id: str, process_id: Optional[str] = None) -> str:
        """Generate unique state key with process isolation."""
        proc_id = process_id or getattr(self.store, "process_id", "default")
        return f"{user_id}:{proc_id}"

    # HORIZON 1: UserProfile Operations (user_profiles table)

    async def user_profile(self, user_id: str, profile: UserProfile) -> bool:
        """CANONICAL: Save Horizon 1 - UserProfile to user_profiles table"""

        if not self.enabled:
            return True

        state_key = self._state_key(user_id)
        emit("persistence", operation="save_profile", key=state_key, status="start")

        try:
            # ONLY persist UserProfile data
            result = await self.store.save_user_profile(state_key, profile)

            emit(
                "persistence",
                operation="save_profile",
                key=state_key,
                status="complete" if result else "failed",
                success=result,
            )
            return result

        except Exception as e:
            emit(
                "persistence", operation="save_profile", key=state_key, status="error", error=str(e)
            )
            return False

    async def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """DEPRECATED: Use persist.load_user_profile() instead. Load Horizon 1 - UserProfile from user_profiles table"""

        if not self.enabled:
            return None

        state_key = self._state_key(user_id)
        emit("persistence", operation="load_profile", key=state_key, status="start")

        try:
            profile = await self.store.load_user_profile(state_key)

            emit(
                "persistence",
                operation="load_profile",
                key=state_key,
                status="complete" if profile else "not_found",
                user_id=profile.user_id if profile else None,
            )
            return profile

        except Exception as e:
            emit(
                "persistence", operation="load_profile", key=state_key, status="error", error=str(e)
            )
            return None

    # HORIZON 2: Workspace Operations (task_workspaces table)

    async def task_workspace(self, task_id: str, user_id: str, workspace: Workspace) -> bool:
        """CANONICAL: Save Horizon 2 - Workspace to task_workspaces table by task_id"""

        if not self.enabled:
            return True

        emit("persistence", operation="save_workspace", key=task_id, status="start")

        try:
            # Save workspace with task_id key for task continuation
            result = await self.store.save_task_workspace(task_id, user_id, workspace)

            emit(
                "persistence",
                operation="save_workspace",
                key=task_id,
                status="complete" if result else "failed",
                success=result,
            )
            return result

        except Exception as e:
            emit(
                "persistence", operation="save_workspace", key=task_id, status="error", error=str(e)
            )
            return False

    async def load_task_workspace(self, task_id: str, user_id: str) -> Optional[Workspace]:
        """CANONICAL: Load Horizon 2 - Workspace from task_workspaces table by task_id"""

        if not self.enabled:
            return None

        emit("persistence", operation="load_workspace", key=task_id, status="start")

        try:
            workspace = await self.store.load_task_workspace(task_id, user_id)

            emit(
                "persistence",
                operation="load_workspace",
                key=task_id,
                status="complete" if workspace else "not_found",
            )
            return workspace

        except Exception as e:
            emit(
                "persistence", operation="load_workspace", key=task_id, status="error", error=str(e)
            )
            return None

    async def delete_task_workspace(self, task_id: str) -> bool:
        """CANONICAL: Delete Horizon 2 - Workspace from task_workspaces table on task completion"""

        if not self.enabled:
            return True

        emit("persistence", operation="delete_workspace", key=task_id, status="start")

        try:
            result = await self.store.delete_task_workspace(task_id)
            emit(
                "persistence",
                operation="delete_workspace",
                key=task_id,
                status="complete" if result else "not_found",
                success=result,
            )
            return result
        except Exception as e:
            emit(
                "persistence",
                operation="delete_workspace",
                key=task_id,
                status="error",
                error=str(e),
            )
            return False

    # LEGACY METHODS (for backward compatibility during transition)

    async def load(self, user_id: str) -> Optional[State]:
        """LEGACY: Load state from persistence - kept for test compatibility"""
        if not self.enabled:
            return None

        # Load user profile
        profile = await self.load_user_profile(user_id)
        if not profile:
            return None

        # Create state with loaded profile
        state = State(query="", user_id=user_id, task_id="")
        state.profile = profile
        return state

    async def save(self, state: State) -> bool:
        """LEGACY: Save both horizons during task execution - will be replaced by autosave"""
        # Save Horizon 1: UserProfile
        profile_saved = await self.user_profile(state.user_id, state.profile)

        # Save Horizon 2: Workspace for task continuation
        workspace_saved = await self.task_workspace(state.task_id, state.user_id, state.workspace)

        # Horizon 3: ExecutionState is NEVER saved - runtime-only

        return profile_saved and workspace_saved

    async def delete(self, user_id: str) -> bool:
        """LEGACY: Delete user profile - workspace cleanup handled by complete_task"""

        if not self.enabled:
            return True

        state_key = self._state_key(user_id)
        emit("persistence", operation="delete", key=state_key, status="start")

        try:
            result = await self.store.delete_user_profile(state_key)
            emit(
                "persistence",
                operation="delete",
                key=state_key,
                status="complete" if result else "not_found",
                success=result,
            )
            return result
        except Exception as e:
            emit("persistence", operation="delete", key=state_key, status="error", error=str(e))
            return False
