"""CLI conversation session management - DATABASE-IS-STATE compliant."""

import json
from pathlib import Path
from typing import Optional

from cogency.config.dataclasses import PathsConfig


class CLISession:
    """Manage CLI conversation continuity via DATABASE-IS-STATE."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        paths = PathsConfig()
        self.session_file = Path(paths.state) / "cli_session.json"

    async def get_conversation_id(self) -> Optional[str]:
        """Get current conversation_id for CLI user."""
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file) as f:
                data = json.load(f)
                return data.get(self.user_id, {}).get("conversation_id")
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    async def save_conversation_id(self, conversation_id: str) -> None:
        """Save conversation_id for CLI user."""
        # Load existing data
        data = {}
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                data = {}

        # Update user's conversation_id
        if self.user_id not in data:
            data[self.user_id] = {}
        data[self.user_id]["conversation_id"] = conversation_id

        # Ensure directory exists
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write
        with open(self.session_file, "w") as f:
            json.dump(data, f)

    async def clear_conversation(self) -> None:
        """Clear current conversation for CLI user."""
        if not self.session_file.exists():
            return

        try:
            with open(self.session_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return

        if self.user_id in data:
            data[self.user_id].pop("conversation_id", None)

            with open(self.session_file, "w") as f:
                json.dump(data, f)


async def get_or_create_conversation_id(user_id: str = "default") -> str:
    """Get existing CLI conversation_id or let State create new one."""
    session = CLISession(user_id)
    return await session.get_conversation_id()


async def save_conversation_id(conversation_id: str, user_id: str = "default") -> None:
    """Save conversation_id from State for CLI continuity."""
    session = CLISession(user_id)
    await session.save_conversation_id(conversation_id)


async def clear_conversation_id(user_id: str = "default") -> None:
    """Clear current conversation for explicit new conversation start."""
    session = CLISession(user_id)
    await session.clear_conversation()
