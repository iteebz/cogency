"""Checkpoint decorator for workflow recovery."""

import hashlib
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

from cogency.state import AgentState

"""Checkpoint storage and state management for workflow recovery."""


def checkpoint(checkpoint_type: str = "tool_execution", interruptible: bool = False):
    """Checkpoint decorator for workflow recovery.

    Args:
        checkpoint_type: Type of checkpoint for categorization
        interruptible: Save checkpoint on success for resumption
    """

    def decorator(func):
        @wraps(func)
        async def checkpointed_func(*args, **kwargs):
            # Extract state from function arguments
            state = args[0] if args else kwargs.get("state")

            if not state or not isinstance(state, AgentState):
                # No state to checkpoint, just run the function
                return await func(*args, **kwargs)

            # Try to resume from existing checkpoint first
            checkpoint_id = checkpointer.find(state)
            if checkpoint_id:
                checkpoint_data = checkpointer.load(checkpoint_id)
                if checkpoint_data and resume(state):
                    # Successfully resumed from checkpoint
                    pass

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Save checkpoint after successful execution if interruptible
                if interruptible:
                    checkpointer.save(state, checkpoint_type)

                return result

            except Exception:
                # Save checkpoint on failure for recovery
                if interruptible:
                    checkpointer.save(state, checkpoint_type)
                raise

        return checkpointed_func

    return decorator


class Checkpoint:
    """Checkpoint storage and retrieval manager."""

    def __init__(self, checkpoint_dir: Optional[Path] = None, session_id: Optional[str] = None):
        from ..config import PathsConfig

        paths = PathsConfig()
        self.checkpoint_dir = checkpoint_dir or Path.home() / paths.checkpoints
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_hours = 1  # Expire checkpoints after 1 hour
        self.session_id = session_id or str(os.getpid())  # Process ID for session isolation

    def _fingerprint(self, state: AgentState) -> str:
        """Generate deterministic fingerprint for state matching with session isolation."""
        return self._generate_fingerprint(state)

    def _generate_fingerprint(self, state: AgentState) -> str:
        """Generate deterministic fingerprint for state matching with session isolation."""
        # v1.0.0: Use stable properties for fingerprint, not dynamic tool state
        components = [
            self.session_id,  # Session isolation prevents state collisions
            state.execution.query,
            state.execution.user_id,
            str(state.execution.iteration),
        ]
        content = "|".join(components)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_checkpoint_path(self, fingerprint: str) -> Path:
        """Get filesystem path for checkpoint."""
        return self.checkpoint_dir / f"{fingerprint}.json"

    def save(self, state: AgentState, checkpoint_type: str = "tool_execution") -> str:
        """Save checkpoint state.

        Args:
            state: Agent state to checkpoint
            checkpoint_type: Type for categorization

        Returns:
            Checkpoint fingerprint
        """
        fingerprint = self._fingerprint(state)
        checkpoint_path = self._get_checkpoint_path(fingerprint)

        # Extract serializable state data - v1.0.0 spec compliant
        checkpoint_data = {
            "fingerprint": fingerprint,
            "timestamp": datetime.now().isoformat(),
            "checkpoint_type": checkpoint_type,
            # ExecutionState data
            "query": state.execution.query,
            "user_id": state.execution.user_id,
            "iteration": state.execution.iteration,
            "mode": state.execution.mode,
            "stop_reason": state.execution.stop_reason,
            "messages": state.execution.messages,
            "response": state.execution.response,
            "pending_calls": state.execution.pending_calls,
            "completed_calls": state.execution.completed_calls,
            # ReasoningContext data
            "reasoning_goal": state.reasoning.goal,
            "reasoning_strategy": state.reasoning.strategy,
            "reasoning_facts": state.reasoning.facts,
            "reasoning_insights": state.reasoning.insights,
            "reasoning_thoughts": state.reasoning.thoughts,
        }

        # Write checkpoint atomically to prevent corruption during interrupts
        temp_path = checkpoint_path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            temp_path.rename(checkpoint_path)  # Atomic rename
        except Exception:
            temp_path.unlink(missing_ok=True)  # Cleanup on failure
            raise

        return fingerprint

    def find(self, state: AgentState) -> Optional[str]:
        """Find matching checkpoint for state."""
        fingerprint = self._fingerprint(state)
        checkpoint_path = self._get_checkpoint_path(fingerprint)

        if not checkpoint_path.exists():
            return None

        # Check if checkpoint is still valid (not expired)
        try:
            with checkpoint_path.open("r") as f:
                checkpoint_data = json.load(f)

            timestamp = datetime.fromisoformat(checkpoint_data["timestamp"])
            if datetime.now() - timestamp > timedelta(hours=self.max_age_hours):
                # Expired checkpoint - remove it
                checkpoint_path.unlink()
                return None

            return fingerprint
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted checkpoint - remove it
            checkpoint_path.unlink()
            return None

    def load(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint data by fingerprint."""
        checkpoint_path = self._get_checkpoint_path(fingerprint)

        if not checkpoint_path.exists():
            return None

        try:
            with checkpoint_path.open("r") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def cleanup_expired(self):
        """Remove expired checkpoints."""
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with checkpoint_file.open("r") as f:
                    data = json.load(f)

                timestamp = datetime.fromisoformat(data["timestamp"])
                if timestamp < cutoff_time:
                    checkpoint_file.unlink()
            except (OSError, json.JSONDecodeError, KeyError, ValueError):
                # Remove corrupted files
                checkpoint_file.unlink()


def resume(state: AgentState) -> bool:
    """Resume workflow from checkpoint.

    Args:
        state: Agent state to restore

    Returns:
        True if successfully resumed
    """
    checkpoint_id = checkpointer.find(state)
    if not checkpoint_id:
        return False

    checkpoint_data = checkpointer.load(checkpoint_id)
    if not checkpoint_data:
        return False

    # Restore state fields from checkpoint - v1.0.0 spec compliant
    try:
        # ExecutionState restoration
        if "iteration" in checkpoint_data:
            state.execution.iteration = checkpoint_data["iteration"]
        if "mode" in checkpoint_data:
            state.execution.mode = checkpoint_data["mode"]
        if "stop_reason" in checkpoint_data:
            state.execution.stop_reason = checkpoint_data["stop_reason"]
        if "response" in checkpoint_data:
            state.execution.response = checkpoint_data["response"]
        if "messages" in checkpoint_data:
            state.execution.messages = checkpoint_data["messages"]
        if "pending_calls" in checkpoint_data:
            state.execution.pending_calls = checkpoint_data["pending_calls"] or []
        if "completed_calls" in checkpoint_data:
            state.execution.completed_calls = checkpoint_data["completed_calls"] or []

        # ReasoningContext restoration
        if "reasoning_goal" in checkpoint_data:
            state.reasoning.goal = checkpoint_data["reasoning_goal"]
        if "reasoning_strategy" in checkpoint_data:
            state.reasoning.strategy = checkpoint_data["reasoning_strategy"]
        if "reasoning_facts" in checkpoint_data:
            state.reasoning.facts = checkpoint_data["reasoning_facts"] or {}
        if "reasoning_insights" in checkpoint_data:
            state.reasoning.insights = checkpoint_data["reasoning_insights"] or []
        if "reasoning_thoughts" in checkpoint_data:
            state.reasoning.thoughts = checkpoint_data["reasoning_thoughts"] or []

        # Add resume context message to LLM
        _add_resume_message(state, checkpoint_data)

        return True

    except Exception:
        # If resume fails, just continue without resuming
        return False


def _add_resume_message(state: AgentState, checkpoint_data: Dict[str, Any]) -> None:
    """Add resume context to message history for LLM awareness."""
    checkpoint_type = checkpoint_data.get("checkpoint_type", "unknown")
    iteration = checkpoint_data.get("iteration", 0)

    # Build recovery message for LLM
    recovery_msg = "RESUMING FROM CHECKPOINT: "

    if checkpoint_type == "tool_execution":
        completed_calls = checkpoint_data.get("completed_calls", [])
        if completed_calls:
            tool_names = [
                call.get("name", "unknown") for call in completed_calls if isinstance(call, dict)
            ]
            recovery_msg += f"Previously completed tools: {', '.join(tool_names)}. "

    recovery_msg += f"Continue from iteration {iteration}. Previous session was interrupted."

    # Add to message history using the proper State method
    state.execution.add_message("system", recovery_msg)


# Global checkpoint manager instance
checkpointer = Checkpoint()
