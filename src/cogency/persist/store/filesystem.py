"""Filesystem persistence store - local state management with file locking."""

import json
import os
import uuid
from dataclasses import asdict
from fcntl import LOCK_EX, LOCK_UN, flock
from pathlib import Path
from typing import Any, Dict, List, Optional

from cogency.state import State

from .base import Store


class Filesystem(Store):
    """File-based state persistence with atomic operations and process isolation."""

    def __init__(self, base_dir: str = ".cogency/state"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.process_id = str(uuid.uuid4())[:8]  # Short process ID

    def _get_state_path(self, state_key: str) -> Path:
        """Get file path for state key with process isolation."""
        # Add process ID to prevent concurrent access issues
        safe_key = state_key.replace(":", "_").replace("/", "_")
        return self.base_dir / f"{safe_key}_{self.process_id}.json"

    async def save(self, state_key: str, state: State) -> bool:
        """Save state atomically with file locking."""
        try:
            state_path = self._get_state_path(state_key)
            temp_path = state_path.with_suffix(".tmp")

            # Prepare serializable state data
            state_data = {
                "state": asdict(state),
                "schema_version": "1.0",
                "process_id": self.process_id,
            }

            # Atomic write: write to temp file first, then rename
            with open(temp_path, "w") as f:
                flock(f.fileno(), LOCK_EX)  # Exclusive lock
                json.dump(state_data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
                flock(f.fileno(), LOCK_UN)  # Release lock

            # Atomic rename
            temp_path.rename(state_path)
            return True

        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            return False

    async def load(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load state with validation."""
        try:
            state_path = self._get_state_path(state_key)
            if not state_path.exists():
                return None

            with open(state_path) as f:
                flock(f.fileno(), LOCK_EX)  # Shared lock for reading
                data = json.load(f)
                flock(f.fileno(), LOCK_UN)

            # Validate schema version
            if data.get("schema_version") != "1.0":
                # Future: add migration logic here
                return None

            return data

        except Exception:
            return None

    async def delete(self, state_key: str) -> bool:
        """Delete state file."""
        try:
            state_path = self._get_state_path(state_key)
            if state_path.exists():
                state_path.unlink()
            return True
        except Exception:
            return False

    async def list_states(self, user_id: str) -> List[str]:
        """List all state files for a user."""
        try:
            # Convert user_id to safe format for pattern matching
            safe_user_id = user_id.replace(":", "_").replace("/", "_")
            pattern = f"{safe_user_id}_*_{self.process_id}.json"
            matches = list(self.base_dir.glob(pattern))

            # Convert back from safe format to original key format
            result = []
            safe_user_id_len = len(safe_user_id)
            for match in matches:
                # Remove process ID suffix
                stem_without_process = match.stem.replace(f"_{self.process_id}", "")
                # Extract the part after the safe user_id
                session_part = stem_without_process[safe_user_id_len + 1 :]  # +1 for the _
                # Reconstruct original key format
                original_key = f"{user_id}:{session_part}"
                result.append(original_key)
            return result
        except Exception:
            return []
