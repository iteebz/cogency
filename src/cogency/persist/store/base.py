"""Base persistence store interface - abstract state storage and retrieval."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from cogency.state import State

# Singleton instance for default persistence store
_persist_instance = None


class Store(ABC):
    """Interface for state persistence stores."""

    @abstractmethod
    async def save(self, state_key: str, state: State) -> bool:
        """Save state."""
        pass

    @abstractmethod
    async def load(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load state. Returns None if not found."""
        pass

    @abstractmethod
    async def delete(self, state_key: str) -> bool:
        """Delete persisted state."""
        pass

    @abstractmethod
    async def list_states(self, user_id: str) -> List[str]:
        """List all state keys for a user."""
        pass


def setup_persistence(persist):
    """Setup persistence backend with auto-detection."""
    if not persist:
        return None
    if hasattr(persist, "store"):  # It's a Persist config object
        return persist

    # Auto-detect default singleton with Persist wrapper
    from cogency import Persist

    global _persist_instance
    if _persist_instance is None:
        from cogency.persist import Filesystem

        _persist_instance = Filesystem()
    return Persist(store=_persist_instance)
