"""State persistence manager - Coordinates state saving/loading with validation."""

from typing import Any, Dict, Optional

from cogency.persistence.backends import FileBackend, StateBackend
from cogency.state import State


class StateManager:
    """Manages state persistence with validation and error handling."""

    def __init__(self, backend: Optional[StateBackend] = None, enabled: bool = True):
        self.backend = backend or FileBackend()
        self.enabled = enabled

    def _generate_state_key(self, user_id: str, process_id: Optional[str] = None) -> str:
        """Generate unique state key with process isolation."""
        proc_id = process_id or getattr(self.backend, "process_id", "default")
        return f"{user_id}:{proc_id}"

    def _create_metadata(self, **kwargs) -> Dict[str, Any]:
        """Create metadata for state persistence."""
        return {
            "llm_provider": kwargs.get("llm_provider", "unknown"),
            "llm_model": kwargs.get("llm_model", "unknown"),
            "tools_count": kwargs.get("tools_count", 0),
            "memory_backend": kwargs.get("memory_backend", "unknown"),
            "saved_at": kwargs.get("timestamp"),
            **{
                k: v
                for k, v in kwargs.items()
                if k
                not in ["llm_provider", "llm_model", "tools_count", "memory_backend", "timestamp"]
            },
        }

    async def save_state(
        self,
        state: State,
        llm_provider: str = "unknown",
        llm_model: str = "unknown",
        tools_count: int = 0,
        memory_backend: str = "unknown",
        timestamp: Optional[str] = None,
        **custom_metadata,
    ) -> bool:
        """Save state with metadata validation."""
        if not self.enabled:
            return True  # Silent success when disabled

        try:
            state_key = self._generate_state_key(state.user_id)
            metadata = self._create_metadata(
                llm_provider=llm_provider,
                llm_model=llm_model,
                tools_count=tools_count,
                memory_backend=memory_backend,
                timestamp=timestamp,
                **custom_metadata,  # Pass custom metadata directly
            )

            return await self.backend.save_state(state_key, state, metadata)

        except Exception:
            # Graceful degradation - don't break agent execution
            return False

    async def load_state(
        self,
        user_id: str,
        validate_llm: bool = True,
        expected_llm_provider: Optional[str] = None,
        expected_llm_model: Optional[str] = None,
    ) -> Optional[State]:
        """Load and validate state."""
        if not self.enabled:
            return None

        try:
            state_key = self._generate_state_key(user_id)
            data = await self.backend.load_state(state_key)

            if not data:
                return None

            # Validate LLM compatibility if requested
            if validate_llm and expected_llm_provider:
                metadata = data.get("metadata", {})
                if metadata.get("llm_provider") != expected_llm_provider:
                    # LLM provider mismatch - reset conversation context
                    return None

                if expected_llm_model and metadata.get("llm_model") != expected_llm_model:
                    # Model mismatch - reset conversation context
                    return None

            # Reconstruct State object from dict
            state_dict = data["state"]

            # Handle dataclass reconstruction carefully
            state = State(
                query=state_dict["query"],
                user_id=state_dict["user_id"],
                messages=state_dict.get("messages", []),
                iteration=state_dict.get("iteration", 0),
                max_iterations=state_dict.get("max_iterations", 10),
                react_mode=state_dict.get("react_mode", "fast"),
                stop_reason=state_dict.get("stop_reason"),
                selected_tools=state_dict.get("selected_tools", []),
                tool_calls=state_dict.get("tool_calls", []),
                result=state_dict.get("result"),
                actions=state_dict.get("actions", []),
                attempts=state_dict.get("attempts", []),
                current_approach=state_dict.get("current_approach", "initial"),
                response=state_dict.get("response"),
                respond_directly=state_dict.get("respond_directly", False),
                verbose=state_dict.get("verbose", True),
                trace=state_dict.get("trace", False),
                callback=None,  # Don't persist callbacks
                notifications=state_dict.get("notifications", []),
            )

            return state

        except Exception:
            # Graceful degradation
            return None

    async def delete_state(self, user_id: str) -> bool:
        """Delete persisted state."""
        if not self.enabled:
            return True

        try:
            state_key = self._generate_state_key(user_id)
            return await self.backend.delete_state(state_key)
        except Exception:
            return False
