"""State persistence manager - Coordinates state saving/loading with validation."""

from typing import Optional

from cogency.persist.store import Filesystem, Store
from cogency.state import AgentMode, State


class Persistence:
    """Manages state persistence with validation and error handling."""

    def __init__(self, store: Optional[Store] = None, enabled: bool = True):
        self.store = store or Filesystem()
        self.enabled = enabled

    def _state_key(self, user_id: str, process_id: Optional[str] = None) -> str:
        """Generate unique state key with process isolation."""
        proc_id = process_id or getattr(self.store, "process_id", "default")
        return f"{user_id}:{proc_id}"

    async def save(self, state: State) -> bool:
        """Save state with v1.0.0 structure."""
        from cogency.events import emit

        if not self.enabled:
            return True

        state_key = self._state_key(state.execution.user_id)
        emit("persistence", operation="save", key=state_key, status="start")

        try:
            # Let the store handle State serialization
            # The filesystem store has the proper serialization logic
            result = await self.store.save(state_key, state)

            emit(
                "persistence",
                operation="save",
                key=state_key,
                status="complete" if result else "failed",
                success=result,
            )
            return result

        except Exception as e:
            emit("persistence", operation="save", key=state_key, status="error", error=str(e))
            return False

    async def load(self, user_id: str) -> Optional[State]:
        """Load state with v1.0.0 structure."""
        from cogency.events import emit

        if not self.enabled:
            return None

        state_key = self._state_key(user_id)
        emit("persistence", operation="load", key=state_key, status="start")

        try:
            data = await self.store.load(state_key)

            if not data:
                emit("persistence", operation="load", key=state_key, status="not_found")
                return None

            # Handle different data formats (backwards compatibility)
            state_dict = data.get("state", data)

            # Reconstruct State with v1.0.0 structure
            # Extract query and user_id from execution data
            if "execution" in state_dict:
                exec_data = state_dict["execution"]
                query = exec_data.get("query", "")
                user_id = exec_data.get("user_id", "default")
            else:
                query = state_dict.get("query", "")
                user_id = state_dict.get("user_id", "default")

            # Create new State
            user_profile = None
            if state_dict.get("user_profile"):
                from cogency.persist.serialize import deserialize_profile

                profile_data = state_dict["user_profile"]
                user_profile = deserialize_profile(profile_data)

            state = State(query=query, user_id=user_id, user_profile=user_profile)

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

            emit(
                "persistence",
                operation="load",
                key=state_key,
                status="complete",
                has_profile=user_profile is not None,
                iteration=state.execution.iteration,
            )
            return state

        except Exception as e:
            emit("persistence", operation="load", key=state_key, status="error", error=str(e))
            # Graceful degradation
            return None

    async def delete(self, user_id: str) -> bool:
        """Delete persisted state."""
        from cogency.events import emit

        if not self.enabled:
            return True

        state_key = self._state_key(user_id)
        emit("persistence", operation="delete", key=state_key, status="start")

        try:
            result = await self.store.delete(state_key)
            emit(
                "persistence",
                operation="delete",
                key=state_key,
                status="complete" if result else "not_found",
                success=result,
            )
            return result
        except Exception as e:
            emit("persistence", operation="delete", key=state_key, status="error", error=str(e))
            return False
