"""Supabase backend - CANONICAL Four-Horizon Split-State Model for production."""

import os
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from cogency.state import Conversation, Profile, Workspace

from . import StateStore


class Supabase(StateStore):
    """CANONICAL Supabase backend implementing Four-Horizon Split-State Model."""

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

        # CANONICAL: Four-Horizon table names
        self.user_profiles_table = f"{table_prefix}user_profiles"
        self.conversations_table = f"{table_prefix}conversations"
        self.task_workspaces_table = f"{table_prefix}task_workspaces"

        # Ensure canonical schema exists
        self._ensure_canonical_schema()

    def _ensure_canonical_schema(self):
        """Ensure CANONICAL Four-Horizon schema exists."""
        # Note: In production Supabase, schema should be created via migration files
        # This is just for development/testing
        pass

    # CANONICAL: Horizon 1 Operations (Profile)

    async def save_user_profile(self, state_key: str, profile: "Profile") -> bool:
        """CANONICAL: Save Horizon 1 - Profile to user_profiles table"""
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

    async def load_user_profile(self, state_key: str) -> Optional["Profile"]:
        """CANONICAL: Load Horizon 1 - Profile from user_profiles table"""
        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.state import Profile

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

    # CANONICAL: Horizon 2 Operations (Conversation)

    async def save_conversation(self, conversation: "Conversation") -> bool:
        """CANONICAL: Save Horizon 2 - Conversation to conversations table"""
        try:
            from dataclasses import asdict

            conversation_dict = asdict(conversation)

            # Handle datetime serialization
            conversation_dict["last_updated"] = conversation.last_updated.isoformat()

            response = (
                self.client.table(self.conversations_table)
                .upsert(
                    {
                        "conversation_id": conversation.conversation_id,
                        "user_id": conversation.user_id,
                        "conversation_data": conversation_dict,
                    }
                )
                .execute()
            )

            return len(response.data) > 0

        except Exception:
            return False

    async def load_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional["Conversation"]:
        """CANONICAL: Load Horizon 2 - Conversation from conversations table"""
        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.state import Conversation

            response = (
                self.client.table(self.conversations_table)
                .select("conversation_data")
                .eq("conversation_id", conversation_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                return None

            conversation_data = response.data[0]["conversation_data"]

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
        """CANONICAL: Delete conversation permanently"""
        try:
            response = (
                self.client.table(self.conversations_table)
                .delete()
                .eq("conversation_id", conversation_id)
                .execute()
            )
            return len(response.data) > 0

        except Exception:
            return False

    # CANONICAL: Horizon 3 Operations (Workspace)

    async def save_task_workspace(self, task_id: str, user_id: str, workspace: "Workspace") -> bool:
        """CANONICAL: Save Horizon 3 - Workspace to task_workspaces table by task_id"""
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
        """CANONICAL: Load Horizon 3 - Workspace from task_workspaces table by task_id"""
        try:
            from dataclasses import fields

            from cogency.state import Workspace

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
        """CANONICAL: Delete Horizon 3 - Workspace on task completion"""
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
