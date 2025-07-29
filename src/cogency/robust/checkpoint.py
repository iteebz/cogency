"""Checkpoint decorator for workflow recovery - focused and clean."""

import hashlib
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

from cogency.state import State

"""Checkpoint storage and state management for workflow recovery."""


def checkpoint(checkpoint_type: str = "tool_execution", interruptible: bool = False):
    """@checkpoint - Workflow recovery with state persistence."""

    def decorator(func):
        @wraps(func)
        async def checkpointed_func(*args, **kwargs):
            # Extract state from function arguments
            state = args[0] if args else kwargs.get("state")

            if not state or not isinstance(state, State):
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
    """Manages checkpoint storage and retrieval."""

    def __init__(self, checkpoint_dir: Optional[Path] = None, session_id: Optional[str] = None):
        self.checkpoint_dir = checkpoint_dir or Path.home() / ".cogency" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_hours = 1  # Expire checkpoints after 1 hour
        self.session_id = session_id or str(os.getpid())  # Process ID for session isolation

    def _generate_fingerprint(self, state: State) -> str:
        """Generate deterministic fingerprint for state matching with session isolation."""
        selected_tools = state.selected_tools or []
        tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in selected_tools]

        components = [
            self.session_id,  # Session isolation prevents state collisions
            state.query,
            str(sorted(tool_names)),
            str(state.iteration),
        ]
        content = "|".join(components)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_checkpoint_path(self, fingerprint: str) -> Path:
        """Get filesystem path for checkpoint."""
        return self.checkpoint_dir / f"{fingerprint}.json"

    def save(self, state: State, checkpoint_type: str = "tool_execution") -> str:
        """Save checkpoint with meaningful progress."""
        fingerprint = self._generate_fingerprint(state)
        checkpoint_path = self._get_checkpoint_path(fingerprint)

        # Extract serializable state data
        checkpoint_data = {
            "fingerprint": fingerprint,
            "timestamp": datetime.now().isoformat(),
            "checkpoint_type": checkpoint_type,
            "query": state.query,
            "user_id": state.user_id,
            "iteration": state.iteration,
            "mode": state.mode,
            "selected_tools": [
                tool.name if hasattr(tool, "name") else str(tool)
                for tool in state.selected_tools or []
            ],
            "tool_calls": state.tool_calls,
            "actions": state.actions,
            "attempts": state.attempts,
            "approach": state.approach,
            "messages": state.messages,
            "result": str(state.result) if state.result else None,
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

    def find(self, state: State) -> Optional[str]:
        """Find matching checkpoint for current state."""
        fingerprint = self._generate_fingerprint(state)
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


def resume(state: State) -> bool:
    """Resume workflow from saved checkpoint if available."""
    checkpoint_id = checkpointer.find(state)
    if not checkpoint_id:
        return False

    checkpoint_data = checkpointer.load(checkpoint_id)
    if not checkpoint_data:
        return False

    # Restore state fields from checkpoint
    try:
        # Core execution state
        if "iteration" in checkpoint_data:
            state.iteration = checkpoint_data["iteration"]
        if "mode" in checkpoint_data:
            state.mode = checkpoint_data["mode"]
        if "approach" in checkpoint_data:
            state.approach = checkpoint_data["approach"]

        # Tool execution state
        if "tool_calls" in checkpoint_data:
            state.tool_calls = checkpoint_data["tool_calls"] or []
        if "actions" in checkpoint_data:
            state.actions = checkpoint_data["actions"]
        if "attempts" in checkpoint_data:
            state.attempts = checkpoint_data["attempts"]

        # Message history
        if "messages" in checkpoint_data:
            state.messages = checkpoint_data["messages"]

        # Add resume context message to LLM
        _add_resume_message(state, checkpoint_data)

        return True

    except Exception:
        # If resume fails, just continue without resuming
        return False


def _add_resume_message(state: State, checkpoint_data: Dict[str, Any]) -> None:
    """Add resume context to message history for LLM awareness."""
    checkpoint_type = checkpoint_data.get("checkpoint_type", "unknown")
    iteration = checkpoint_data.get("iteration", 0)

    # Build recovery message for LLM
    recovery_msg = "RESUMING FROM CHECKPOINT: "

    if checkpoint_type == "tool_execution":
        tool_calls = checkpoint_data.get("tool_calls", [])
        if tool_calls:
            tool_names = [
                call.get("name", "unknown") for call in tool_calls if isinstance(call, dict)
            ]
            recovery_msg += f"Previously completed tools: {', '.join(tool_names)}. "

    recovery_msg += f"Continue from iteration {iteration}. Previous session was interrupted."

    # Add to message history using the proper State method
    state.add_message("system", recovery_msg)


# Global checkpoint manager instance
checkpointer = Checkpoint()
