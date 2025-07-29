from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from cogency.state import State

# Singleton instance for default persistence backend
_persist_instance = None


class Store(ABC):
    """Interface for state persistence backends."""

    @abstractmethod
    async def save(self, state_key: str, state: State, metadata: Dict[str, Any]) -> bool:
        """Save state with metadata."""
        pass

    @abstractmethod
    async def load_state(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load state and metadata. Returns None if not found."""
        pass

    @abstractmethod
    async def delete_state(self, state_key: str) -> bool:
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
    if hasattr(persist, "backend"):  # It's a Persist config object
        return persist

    # Auto-detect default singleton with Persist wrapper
    from cogency import Persist

    global _persist_instance
    if _persist_instance is None:
        from cogency.persist import Filesystem

        _persist_instance = Filesystem()
    return Persist(backend=_persist_instance)
