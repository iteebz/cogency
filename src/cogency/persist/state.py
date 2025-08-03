"""State persistence manager - Coordinates state saving/loading with validation."""

from typing import Optional

from cogency.persist.store import Filesystem, Store
from cogency.state import AgentMode, AgentState


class StatePersistence:
    """Manages state persistence with validation and error handling."""

    def __init__(self, store: Optional[Store] = None, enabled: bool = True):
        self.store = store or Filesystem()
        self.enabled = enabled

    def _state_key(self, user_id: str, process_id: Optional[str] = None) -> str:
        """Generate unique state key with process isolation."""
        proc_id = process_id or getattr(self.store, "process_id", "default")
        return f"{user_id}:{proc_id}"

    async def save(self, state: AgentState) -> bool:
        """Save state with v1.0.0 structure."""
        if not self.enabled:
            return True

        try:
            state_key = self._state_key(state.execution.user_id)

            # Let the store handle AgentState serialization
            # The filesystem store has the proper serialization logic
            return await self.store.save(state_key, state)

        except Exception:
            return False

    async def load(self, user_id: str) -> Optional[AgentState]:
        """Load state with v1.0.0 structure."""
        if not self.enabled:
            return None

        try:
            state_key = self._state_key(user_id)
            data = await self.store.load(state_key)

            if not data:
                return None

            # Handle different data formats (backwards compatibility)
            state_dict = data.get("state", data)

            # Reconstruct AgentState with v1.0.0 structure
            # Extract query and user_id from execution data
            if "execution" in state_dict:
                exec_data = state_dict["execution"]
                query = exec_data.get("query", "")
                user_id = exec_data.get("user_id", "default")
            else:
                query = state_dict.get("query", "")
                user_id = state_dict.get("user_id", "default")

            # Create new AgentState
            user_profile = None
            if state_dict.get("user_profile"):
                from cogency.persist.serialize import deserialize_profile

                profile_data = state_dict["user_profile"]
                user_profile = deserialize_profile(profile_data)

            state = AgentState(query=query, user_id=user_id, user_profile=user_profile)

            # Restore execution state
            if "execution" in state_dict:
                exec_data = state_dict["execution"]
                state.execution.iteration = exec_data.get("iteration", 0)
                # Handle mode conversion from string to enum
                mode_str = exec_data.get("mode", "adapt")
                try:
                    state.execution.mode = AgentMode(mode_str)
                except ValueError:
                    state.execution.mode = AgentMode.ADAPT
                state.execution.stop_reason = exec_data.get("stop_reason")
                state.execution.response = exec_data.get("response")
                state.execution.messages = exec_data.get("messages", [])
                state.execution.pending_calls = exec_data.get("pending_calls", [])
                state.execution.completed_calls = exec_data.get("completed_calls", [])

            # Restore reasoning state
            if "reasoning" in state_dict:
                reasoning_data = state_dict["reasoning"]
                state.reasoning.goal = reasoning_data.get("goal", query)
                state.reasoning.strategy = reasoning_data.get("strategy", "")
                state.reasoning.facts = reasoning_data.get("facts", {})
                state.reasoning.insights = reasoning_data.get("insights", [])
                state.reasoning.thoughts = reasoning_data.get("thoughts", [])

            return state

        except Exception as e:
            # Graceful degradation - for debugging
            print(f"Debug: Load failed with {e}")
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
