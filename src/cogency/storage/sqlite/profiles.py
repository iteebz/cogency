"""SQLite profile operations - user identity persistence."""

import json
from typing import TYPE_CHECKING, Optional

import aiosqlite

if TYPE_CHECKING:
    from cogency.memory import Profile

from ...events.orchestration import extract_delete_data, extract_profile_data, state_event
from .base import SQLiteBase


class ProfileOperations(SQLiteBase):
    """SQLite operations for user profile persistence."""

    @state_event("profile_saved", extract_profile_data)
    async def save_profile(self, state_key: str, profile: "Profile") -> bool:
        """Save user profile to storage."""
        await self._ensure_schema()

        try:
            from dataclasses import asdict

            user_id = state_key.split(":")[0]
            profile_dict = asdict(profile)

            # Handle datetime serialization
            profile_dict["created_at"] = profile.created_at.isoformat()
            profile_dict["last_updated"] = profile.last_updated.isoformat()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles (user_id, profile_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, json.dumps(profile_dict)),
                )
                await db.commit()

            return True

        except Exception:
            return False

    async def load_profile(self, state_key: str) -> Optional["Profile"]:
        """Load user profile from storage."""
        await self._ensure_schema()

        try:
            from dataclasses import fields
            from datetime import datetime

            from cogency.memory import Profile

            user_id = state_key.split(":")[0]

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT profile_data FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                profile_data = json.loads(row[0])

                # Reconstruct Profile with datetime deserialization
                profile_kwargs = {}
                for field in fields(Profile):
                    if field.name in profile_data:
                        value = profile_data[field.name]
                        # Handle datetime deserialization
                        if field.name in ["created_at", "last_updated"] and isinstance(value, str):
                            value = datetime.fromisoformat(value)
                        profile_kwargs[field.name] = value

                return Profile(**profile_kwargs)

        except Exception:
            return None

    @state_event("profile_deleted", extract_delete_data)
    async def delete_profile(self, state_key: str) -> bool:
        """Delete user profile permanently."""
        await self._ensure_schema()

        try:
            user_id = state_key.split(":")[0]

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
                await db.commit()
                return cursor.rowcount > 0

        except Exception:
            return False
