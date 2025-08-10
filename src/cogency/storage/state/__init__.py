"""State storage interface for agent persistence.

Provides StateStore interface for different backends:
- SQLite: Local file-based state storage
- Supabase: Cloud-based state storage

Example:
    Using with SQLite:

    ```python
    from cogency.storage.state import SQLite

    store = SQLite("agent_state.db")
    await store.save_user_profile(user_id, profile)
    ```

    Using with Supabase:

    ```python
    from cogency.storage.state import Supabase

    store = Supabase(url=url, key=key)
    profile = await store.load_user_profile(user_id)
    ```
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from cogency.state import Conversation, Profile, Workspace


class StateStore(ABC):
    """State storage interface for agent persistence."""

    # Profile Operations (permanent user identity)

    @abstractmethod
    async def save_user_profile(self, state_key: str, profile: "Profile") -> bool:
        """Save user profile to storage"""
        pass

    @abstractmethod
    async def load_user_profile(self, state_key: str) -> Optional["Profile"]:
        """Load user profile from storage"""
        pass

    @abstractmethod
    async def delete_user_profile(self, state_key: str) -> bool:
        """Delete user profile permanently"""
        pass

    # Conversation Operations (persistent message history)

    @abstractmethod
    async def save_conversation(self, conversation: "Conversation") -> bool:
        """Save conversation to storage"""
        pass

    @abstractmethod
    async def load_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional["Conversation"]:
        """Load conversation from storage"""
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation permanently"""
        pass

    # Workspace Operations (task-scoped context)

    @abstractmethod
    async def save_task_workspace(self, task_id: str, user_id: str, workspace: "Workspace") -> bool:
        """Save task workspace to storage"""
        pass

    @abstractmethod
    async def load_task_workspace(self, task_id: str, user_id: str) -> Optional["Workspace"]:
        """Load task workspace from storage"""
        pass

    @abstractmethod
    async def delete_task_workspace(self, task_id: str) -> bool:
        """Delete task workspace on completion"""
        pass

    # Utility Operations

    @abstractmethod
    async def list_user_workspaces(self, user_id: str) -> List[str]:
        """List all task_ids for user's active workspaces"""
        pass


def _setup_persist(config):
    """Setup persistence backend from config.

    Args:
        config: Configuration dictionary or PersistConfig object

    Returns:
        StateStore instance or None
    """
    # Handle PersistConfig objects
    if hasattr(config, "enabled"):
        if not config.enabled:
            return None
        if hasattr(config, "store") and config.store:
            return config.store
        # Default to SQLite if enabled but no store specified
        return SQLite()

    # Handle dictionary config
    if not config.get("persistence", {}).get("enabled", False):
        return None

    backend = config.get("persistence", {}).get("backend", "sqlite")

    if backend == "sqlite":
        path = config.get("persistence", {}).get("path", "agent_state.db")
        return SQLite(path)
    elif backend == "supabase":
        url = config.get("persistence", {}).get("url")
        key = config.get("persistence", {}).get("key")
        return Supabase(url, key)

    return None


# Import implementations at end to avoid circular dependencies
from .sqlite import SQLite  # noqa: E402
from .supabase import Supabase  # noqa: E402

__all__ = [
    "StateStore",
    "SQLite",
    "Supabase",
]
