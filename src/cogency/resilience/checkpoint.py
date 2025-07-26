"""Checkpoint storage and state management for workflow recovery."""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from cogency.state import State


class CheckpointManager:
    """Manages checkpoint storage and retrieval."""

    def __init__(self, checkpoint_dir: Optional[Path] = None, session_id: Optional[str] = None):
        self.checkpoint_dir = checkpoint_dir or Path.home() / ".cogency" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_hours = 1  # Expire checkpoints after 1 hour
        self.session_id = session_id or str(os.getpid())  # Process ID for session isolation

    def _generate_fingerprint(self, state: State) -> str:
        """Generate deterministic fingerprint for state matching with session isolation."""
        # Handle both real State objects and mocks
        selected_tools = getattr(state, "selected_tools", []) or []
        tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in selected_tools]

        components = [
            self.session_id,  # Session isolation prevents state collisions
            state.get("query", ""),
            str(sorted(tool_names)),
            str(state.get("current_iteration", 0)),
        ]
        content = "|".join(components)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_checkpoint_path(self, fingerprint: str) -> Path:
        """Get filesystem path for checkpoint."""
        return self.checkpoint_dir / f"{fingerprint}.json"

    def save_checkpoint(self, state: State, checkpoint_type: str = "tool_execution") -> str:
        """Save checkpoint with meaningful progress."""
        fingerprint = self._generate_fingerprint(state)
        checkpoint_path = self._get_checkpoint_path(fingerprint)

        # Extract serializable state data
        checkpoint_data = {
            "fingerprint": fingerprint,
            "timestamp": datetime.now().isoformat(),
            "checkpoint_type": checkpoint_type,
            "query": state.get("query", ""),
            "current_iteration": state.get("current_iteration", 0),
            "react_mode": state.get("react_mode", "fast"),
            "selected_tools": [
                tool.name if hasattr(tool, "name") else str(tool)
                for tool in state.selected_tools or []
            ],
            "cognition": {
                "iterations": state.cognition.iterations if hasattr(state, "cognition") else [],
                "failed_attempts": state.cognition.failed_attempts
                if hasattr(state, "cognition")
                else [],
                "current_approach": getattr(state.cognition, "current_approach", "unified_react")
                if hasattr(state, "cognition")
                else "unified_react",
                "react_mode": getattr(state.cognition, "react_mode", "fast")
                if hasattr(state, "cognition")
                else "fast",
            },
            "execution_results": state.get("execution_results"),
            "prev_tool_calls": state.get("prev_tool_calls", []),
            "context_messages": state.context.messages
            if hasattr(state, "context") and hasattr(state.context, "messages")
            else [],
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

    def find_checkpoint(self, state: State) -> Optional[str]:
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

    def load_checkpoint(self, fingerprint: str) -> Optional[Dict[str, Any]]:
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


def resume(state: "State") -> bool:
    """Resume workflow from saved checkpoint if available."""
    checkpoint_id = checkpoints.find_checkpoint(state)
    if not checkpoint_id:
        return False

    checkpoint_data = checkpoints.load_checkpoint(checkpoint_id)
    if not checkpoint_data:
        return False

    # Restore state from checkpoint
    state.flow["resume_from_checkpoint"] = True
    state.flow["checkpoint_id"] = checkpoint_id

    # Restore flow data
    for key, value in checkpoint_data.items():
        if key not in ["fingerprint", "timestamp", "checkpoint_type"]:
            if key == "cognition":
                # Restore cognition state
                if value:
                    state.cognition.iterations = value.get("iterations", [])
                    state.cognition.failed_attempts = value.get("failed_attempts", [])
                    state.cognition.current_approach = value.get(
                        "current_approach", "unified_react"
                    )
                    state.cognition.react_mode = value.get("react_mode", "fast")
            elif key == "context_messages":
                # Restore context messages
                if hasattr(state.context, "messages") and value:
                    state.context.messages = value
            else:
                # Restore other flow data
                state.flow[key] = value

    # Add recovery context for LLM
    _add_checkpoint_context(state, checkpoint_data)

    return True


def _add_checkpoint_context(state: "State", checkpoint_data: Dict[str, Any]) -> None:
    """Add checkpoint recovery context for LLM communication."""
    checkpoint_type = checkpoint_data.get("checkpoint_type", "unknown")
    iteration = checkpoint_data.get("current_iteration", 0)

    # Build recovery message for LLM
    recovery_msg = "RESUMING FROM CHECKPOINT: "

    if checkpoint_type == "act":
        prev_tools = checkpoint_data.get("prev_tool_calls", [])
        if prev_tools:
            tool_names = [
                call.get("name", "unknown") for call in prev_tools if isinstance(call, dict)
            ]
            recovery_msg += f"Previously completed tools: {', '.join(tool_names)}. "

    recovery_msg += f"Continue from iteration {iteration}. Previous network failure resolved."

    # Add to context as system message
    if hasattr(state.context, "messages"):
        state.context.messages.insert(0, {"role": "system", "content": recovery_msg})


# Global checkpoint manager instance
checkpoints = CheckpointManager()
