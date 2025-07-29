"""State persistence manager - Coordinates state saving/loading with validation."""

from typing import Optional

from cogency.persist.store import Filesystem, Store
from cogency.state import State


class StatePersistence:
    """Manages state persistence with validation and error handling."""

    def __init__(self, store: Optional[Store] = None, enabled: bool = True):
        self.store = store or Filesystem()
        self.enabled = enabled

    def _state_key(self, user_id: str, process_id: Optional[str] = None) -> str:
        """Generate unique state key with process isolation."""
        proc_id = process_id or getattr(self.store, "process_id", "default")
        return f"{user_id}:{proc_id}"

    async def save(self, state: State) -> bool:
        """Save state."""
        if not self.enabled:
            return True

        try:
            state_key = self._state_key(state.user_id)
            return await self.store.save(state_key, state)

        except Exception:
            return False

    async def load(self, user_id: str) -> Optional[State]:
        """Load state."""
        if not self.enabled:
            return None

        try:
            state_key = self._state_key(user_id)
            data = await self.store.load(state_key)

            if not data:
                return None

            # Reconstruct State object from dict
            state_dict = data["state"]

            # Handle dataclass reconstruction carefully
            state = State(
                query=state_dict["query"],
                user_id=state_dict["user_id"],
                messages=state_dict.get("messages", []),
                iteration=state_dict.get("iteration", 0),
                depth=state_dict.get("depth", 10),
                mode=state_dict.get("mode", "fast"),
                stop_reason=state_dict.get("stop_reason"),
                selected_tools=state_dict.get("selected_tools", []),
                tool_calls=state_dict.get("tool_calls", []),
                result=state_dict.get("result"),
                actions=state_dict.get("actions", []),
                attempts=state_dict.get("attempts", []),
                response=state_dict.get("response"),
                respond_directly=state_dict.get("respond_directly", False),
                notify=state_dict.get("notify", True),
                debug=state_dict.get("debug", False),
                callback=None,  # Don't persist callbacks
                notifications=state_dict.get("notifications", []),
            )

            return state

        except Exception:
            # Graceful degradation
            return None

    async def delete(self, user_id: str) -> bool:
        """Delete persisted state."""
        if not self.enabled:
            return True

        try:
            state_key = self._state_key(user_id)
            return await self.store.delete(state_key)
        except Exception:
            return False
