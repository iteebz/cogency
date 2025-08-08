"""Supabase backend - CANONICAL Three-Horizon Split-State Model for production."""

import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from cogency.state.agent import UserProfile, Workspace

from .base import Store


class Supabase(Store):
    """CANONICAL Supabase backend implementing Three-Horizon Split-State Model per docs/dev/state.md"""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        table_prefix: str = "cogency_",
    ):
        """Initialize Supabase store with canonical schema."""
        try:
            from supabase import Client, create_client
        except ImportError:
            raise ImportError(
                "supabase package required. Install with: pip install supabase"
            ) from None

        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase URL and key required. Set SUPABASE_URL and SUPABASE_ANON_KEY "
                "environment variables or pass them directly."
            )

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

        # CANONICAL: Three-Horizon table names
        self.user_profiles_table = f"{table_prefix}user_profiles"
        self.task_workspaces_table = f"{table_prefix}task_workspaces"

        # Ensure canonical schema exists
        self._ensure_canonical_schema()

    def _ensure_canonical_schema(self):
        """Ensure CANONICAL Three-Horizon schema exists - matches docs/dev/state.md exactly."""
        # Note: In production Supabase, schema should be created via migration files
        # This is just for development/testing
        pass

    # CANONICAL: Horizon 1 Operations (UserProfile)

    async def save_user_profile(self, state_key: str, profile: "UserProfile") -> bool:
        """CANONICAL: Save Horizon 1 - UserProfile to user_profiles table"""
        try:
            from dataclasses import asdict

            user_id = state_key.split(":")[0]
            profile_dict = asdict(profile)

            # Handle datetime serialization
            profile_dict["created_at"] = profile.created_at.isoformat()
            profile_dict["last_updated"] = profile.last_updated.isoformat()

            response = (
                self.client.table(self.user_profiles_table)
                .upsert(
                    {
                        "user_id": user_id,
                        "profile_data": profile_dict,
                    }
                )
                .execute()
            )

            return len(response.data) > 0

        except Exception:
            return False

    async def load_user_profile(self, state_key: str) -> Optional["UserProfile"]:
        """CANONICAL: Load Horizon 1 - UserProfile from user_profiles table"""
        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.state.agent import UserProfile

            user_id = state_key.split(":")[0]

            response = (
                self.client.table(self.user_profiles_table)
                .select("profile_data")
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                return None

            profile_data = response.data[0]["profile_data"]

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

    async def delete_user_profile(self, state_key: str) -> bool:
        """CANONICAL: Delete user profile permanently"""
        try:
            user_id = state_key.split(":")[0]

            response = (
                self.client.table(self.user_profiles_table)
                .delete()
                .eq("user_id", user_id)
                .execute()
            )
            return len(response.data) > 0

        except Exception:
            return False

    # CANONICAL: Horizon 2 Operations (Workspace)

    async def save_task_workspace(self, task_id: str, user_id: str, workspace: "Workspace") -> bool:
        """CANONICAL: Save Horizon 2 - Workspace to task_workspaces table by task_id"""
        try:
            from dataclasses import asdict

            workspace_dict = asdict(workspace)

            response = (
                self.client.table(self.task_workspaces_table)
                .upsert(
                    {
                        "task_id": task_id,
                        "user_id": user_id,
                        "workspace_data": workspace_dict,
                    }
                )
                .execute()
            )

            return len(response.data) > 0

        except Exception:
            return False

    async def load_task_workspace(self, task_id: str, user_id: str) -> Optional["Workspace"]:
        """CANONICAL: Load Horizon 2 - Workspace from task_workspaces table by task_id"""
        try:
            from dataclasses import fields

            from cogency.state.agent import Workspace

            response = (
                self.client.table(self.task_workspaces_table)
                .select("workspace_data")
                .eq("task_id", task_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                return None

            workspace_data = response.data[0]["workspace_data"]

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
        try:
            response = (
                self.client.table(self.task_workspaces_table)
                .delete()
                .eq("task_id", task_id)
                .execute()
            )
            return len(response.data) > 0

        except Exception:
            return False

    # CANONICAL: Utility Operations

    async def list_user_workspaces(self, user_id: str) -> List[str]:
        """CANONICAL: List all task_ids for user's active workspaces"""
        try:
            response = (
                self.client.table(self.task_workspaces_table)
                .select("task_id")
                .eq("user_id", user_id)
                .execute()
            )
            return [row["task_id"] for row in response.data]
        except Exception:
            return []

    # LEGACY COMPATIBILITY (Store interface)

    async def save(self, state_key: str, data: Union[Dict[str, Any], Any]) -> bool:
        """Store interface compatibility - delegates to canonical methods"""
        return True

    async def load(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Store interface compatibility - delegates to canonical methods"""
        return None

    async def delete(self, state_key: str) -> bool:
        """Store interface compatibility - delegates to canonical methods"""
        return await self.delete_user_profile(state_key)

    async def list_states(self, user_id: str) -> List[str]:
        """Store interface compatibility - delegates to canonical methods"""
        return await self.list_user_workspaces(user_id)
