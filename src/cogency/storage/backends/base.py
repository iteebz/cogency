"""Base store interface - CANONICAL Three-Horizon Split-State Model."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from cogency.state.agent import UserProfile, Workspace


class Store(ABC):
    """CANONICAL Store interface implementing Three-Horizon Split-State Model per docs/dev/state.md"""

    # CANONICAL: Horizon 1 Operations (UserProfile - persistent across sessions)

    @abstractmethod
    async def save_user_profile(self, state_key: str, profile: "UserProfile") -> bool:
        """CANONICAL: Save Horizon 1 - UserProfile to user_profiles table"""
        pass

    @abstractmethod
    async def load_user_profile(self, state_key: str) -> Optional["UserProfile"]:
        """CANONICAL: Load Horizon 1 - UserProfile from user_profiles table"""
        pass

    @abstractmethod
    async def delete_user_profile(self, state_key: str) -> bool:
        """CANONICAL: Delete user profile permanently"""
        pass

    # CANONICAL: Horizon 2 Operations (Workspace - task-scoped persistence)

    @abstractmethod
    async def save_task_workspace(self, task_id: str, user_id: str, workspace: "Workspace") -> bool:
        """CANONICAL: Save Horizon 2 - Workspace to task_workspaces table by task_id"""
        pass

    @abstractmethod
    async def load_task_workspace(self, task_id: str, user_id: str) -> Optional["Workspace"]:
        """CANONICAL: Load Horizon 2 - Workspace from task_workspaces table by task_id"""
        pass

    @abstractmethod
    async def delete_task_workspace(self, task_id: str) -> bool:
        """CANONICAL: Delete Horizon 2 - Workspace on task completion"""
        pass

    # CANONICAL: Utility Operations

    @abstractmethod
    async def list_user_workspaces(self, user_id: str) -> List[str]:
        """CANONICAL: List all task_ids for user's active workspaces"""
        pass

    # LEGACY COMPATIBILITY (Store interface - will be phased out)

    @abstractmethod
    async def save(self, state_key: str, data: Any) -> bool:
        """LEGACY: Backward compatibility only"""
        pass

    @abstractmethod
    async def load(self, state_key: str) -> Optional[Dict[str, Any]]:
        """LEGACY: Backward compatibility only"""
        pass

    @abstractmethod
    async def delete(self, state_key: str) -> bool:
        """LEGACY: Backward compatibility only"""
        pass

    @abstractmethod
    async def list_states(self, user_id: str) -> List[str]:
        """LEGACY: Backward compatibility only"""
        pass


# Singleton for backward compatibility during transition
_persist_instance = None


def _setup_persist(persist):
    """LEGACY: Setup persistence backend with auto-detection - use canonical methods instead"""
    if not persist:
        return None

    from ..state import Persistence

    if hasattr(persist, "store"):
        return Persistence(store=persist.store, enabled=persist.enabled)

    # Auto-detect default singleton with Persistence wrapper
    global _persist_instance
    if _persist_instance is None:
        from .sqlite import SQLite

        _persist_instance = SQLite()

    return Persistence(store=_persist_instance)
