"""Supabase persistence store - cloud-native state sync with SQLite compatibility."""

import os
from typing import Any, Dict, List, Optional, Union

from cogency.persist.serialize import serialize_dataclass, serialize_profile
from cogency.state import AgentState

from .base import Store


class SupabaseStore(Store):
    """Supabase-based state persistence with same JSON blob structure as SQLite."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        table_prefix: str = "cogency_",
    ):
        """Initialize Supabase store.

        Args:
            supabase_url: Supabase project URL (or from SUPABASE_URL env var)
            supabase_key: Supabase anon key (or from SUPABASE_ANON_KEY env var)
            table_prefix: Prefix for table names
        """
        try:
            from supabase import Client, create_client
        except ImportError:
            raise ImportError(
                "supabase package required for SupabaseStore. " "Install with: pip install supabase"
            ) from None

        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase URL and key required. Set SUPABASE_URL and SUPABASE_ANON_KEY "
                "environment variables or pass them directly."
            )

        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.states_table = f"{table_prefix}agent_states"
        self.profiles_table = f"{table_prefix}user_profiles"

    async def save(self, state_key: str, state: Union[AgentState, Dict[str, Any]]) -> bool:
        """Save state to Supabase with upsert."""
        try:
            # Handle profile keys
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

            user_id = state_key.split(":")[0]

            # Upsert to Supabase
            result = (
                self.client.table(self.states_table)
                .upsert({"user_id": user_id, "state_data": state_data})
                .execute()
            )

            return len(result.data) > 0

        except Exception:
            return False

    async def _save_profile(self, state_key: str, profile_data: Dict[str, Any]) -> bool:
        """Save user profile to Supabase."""
        try:
            user_id = state_key.replace("profile:", "")

            result = (
                self.client.table(self.profiles_table)
                .upsert(
                    {
                        "user_id": user_id,
                        "profile_data": profile_data.get("state", profile_data),
                    }
                )
                .execute()
            )

            return len(result.data) > 0

        except Exception:
            return False

    async def load(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load state from Supabase."""
        try:
            # Handle profile keys
            if state_key.startswith("profile:"):
                return await self._load_profile(state_key)

            user_id = state_key.split(":")[0]

            result = (
                self.client.table(self.states_table)
                .select("state_data")
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                return {"state": result.data[0]["state_data"]}
            return None

        except Exception:
            return None

    async def _load_profile(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load user profile from Supabase."""
        try:
            user_id = state_key.replace("profile:", "")

            result = (
                self.client.table(self.profiles_table)
                .select("profile_data")
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                return {"state": result.data[0]["profile_data"]}
            return None

        except Exception:
            return None

    async def delete(self, state_key: str) -> bool:
        """Delete state from Supabase."""
        try:
            if state_key.startswith("profile:"):
                user_id = state_key.replace("profile:", "")
                table = self.profiles_table
            else:
                user_id = state_key.split(":")[0]
                table = self.states_table

            result = self.client.table(table).delete().eq("user_id", user_id).execute()
            return len(result.data) > 0

        except Exception:
            return False

    async def list_states(self, user_id: str) -> List[str]:
        """List all state keys for a user."""
        try:
            result = (
                self.client.table(self.states_table)
                .select("user_id")
                .like("user_id", f"{user_id}%")
                .execute()
            )

            # Return state keys in original format
            return [f"{row['user_id']}:default" for row in result.data]

        except Exception:
            return []

    async def sync_from_sqlite(self, sqlite_store) -> Dict[str, Any]:
        """Sync states from SQLite to Supabase for cloud backup."""
        sync_report = {"states_synced": 0, "profiles_synced": 0, "errors": []}

        try:
            # Get all states from SQLite
            states = await sqlite_store.query_states(limit=10000)

            for state_info in states:
                try:
                    state_key = f"{state_info['user_id']}:default"
                    state_data = {"state": state_info["state_data"]}

                    success = await self.save(state_key, state_data)
                    if success:
                        sync_report["states_synced"] += 1
                    else:
                        sync_report["errors"].append(f"Failed to sync state: {state_key}")

                except Exception as e:
                    sync_report["errors"].append(
                        f"Error syncing state {state_info.get('user_id')}: {str(e)}"
                    )

        except Exception as e:
            sync_report["errors"].append(f"Error querying SQLite states: {str(e)}")

        return sync_report
