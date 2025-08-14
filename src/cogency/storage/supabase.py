"""Supabase backend - domain-centric persistence for production."""

import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from cogency.context.conversation import Conversation
    from cogency.context.memory.memory import Profile
    from cogency.context.working import WorkingState


class Supabase:
    """Supabase backend implementing domain-centric persistence."""

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

        # Domain persistence table names
        self.user_profiles_table = f"{table_prefix}user_profiles"
        self.conversations_table = f"{table_prefix}conversations"
        self.task_workspaces_table = f"{table_prefix}task_workspaces"

        # Ensure schema exists
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure domain persistence schema exists."""
        # Note: In production Supabase, schema should be created via migration files
        # This is just for development/testing
        pass

    # Profile Operations

    async def save_profile(self, state_key: str, profile: "Profile") -> bool:
        """Save user profile to storage."""
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

    async def load_profile(self, state_key: str) -> Optional["Profile"]:
        """Load user profile from storage."""
        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.context.memory.memory import Profile

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

    async def delete_profile(self, state_key: str) -> bool:
        """Delete user profile permanently."""
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

    # Conversation Operations

    async def save_conversation(self, conversation: "Conversation") -> bool:
        """Save conversation to storage."""
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
        """Load conversation from storage."""
        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.context.conversation import Conversation

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
        """Delete conversation permanently."""
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

    # Workspace Operations (DEPRECATED - domain violations)

    async def save_workspace(self, working_state: "WorkingState") -> bool:
        """Save workspace to storage - DEPRECATED: Use domain operations."""
        # This entire method should be removed - WorkingState operations should be in
        # context.working domain, not in generic storage backend
        raise NotImplementedError("Use domain operations in context.working instead")

    async def load_workspace(self, task_id: str, user_id: str) -> Optional["WorkingState"]:
        """Load workspace from storage - DEPRECATED: Use domain operations."""
        # This entire method should be removed - WorkingState operations should be in
        # context.working domain, not in generic storage backend
        raise NotImplementedError("Use domain operations in context.working instead")

    async def delete_workspace(self, conversation_id: str) -> bool:
        """Delete workspace - DEPRECATED: Use domain operations."""
        # This entire method should be removed - WorkingState operations should be in
        # context.working domain, not in generic storage backend
        raise NotImplementedError("Use domain operations in context.working instead")

    # Utility Operations

    async def list_conversations(self, user_id: str, limit: int = 50) -> list[dict[str, str]]:
        """List conversations for user with metadata."""
        try:
            response = (
                self.client.table(self.conversations_table)
                .select("conversation_id, conversation_data, updated_at")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )

            conversations = []
            for row in response.data:
                conversation_data = row["conversation_data"]
                title = self._extract_conversation_title(conversation_data)

                conversations.append(
                    {
                        "conversation_id": row["conversation_id"],
                        "title": title,
                        "updated_at": row["updated_at"],
                        "message_count": len(conversation_data.get("messages", [])),
                    }
                )

            return conversations
        except Exception:
            return []

    def _extract_conversation_title(self, conversation_data: dict) -> str:
        """Extract meaningful title from conversation data."""
        messages = conversation_data.get("messages", [])
        if not messages:
            return "Empty conversation"

        # Get first user message for title
        first_user_msg = None
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content"):
                first_user_msg = msg["content"]
                break

        if not first_user_msg:
            return "No user messages"

        # Create title from first message
        title = first_user_msg.strip()
        if len(title) > 60:
            title = title[:57] + "..."

        return title
