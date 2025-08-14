"""SQLite profile operations - user identity persistence."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiosqlite

if TYPE_CHECKING:
    from cogency.context.memory import Profile

from ...events.orchestration import domain_event, extract_delete_data, extract_profile_data


async def _ensure_schema(db_path: str):
    """Ensure profile schema exists."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                profile_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


def _get_db_path(db_path: str = None) -> str:
    """Get database path with defaults."""
    if db_path is None:
        from cogency.config.paths import paths

        base_path = Path(paths.base_dir)
        base_path.mkdir(exist_ok=True)
        db_path = base_path / "store.db"

    if db_path == ":memory:" or str(db_path).startswith(":memory:"):
        return str(db_path)
    return str(Path(db_path).expanduser().resolve())


async def create_profile(user_id: str, db_path: str = None) -> "Profile":
    """Create new user profile."""
    from cogency.context.memory import Profile

    return Profile(user_id=user_id)


@domain_event("profile_saved", extract_profile_data)
async def save_profile(state_key: str, profile: "Profile", db_path: str = None) -> bool:
    """Save user profile to storage."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        from dataclasses import asdict

        user_id = state_key.split(":")[0]
        profile_dict = asdict(profile)

        # Handle datetime serialization
        profile_dict["created_at"] = profile.created_at.isoformat()
        profile_dict["last_updated"] = profile.last_updated.isoformat()

        async with aiosqlite.connect(db_path) as db:
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


async def load_profile(state_key: str, db_path: str = None) -> Optional["Profile"]:
    """Load user profile from storage."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        from dataclasses import fields
        from datetime import datetime

        from cogency.context.memory import Profile

        user_id = state_key.split(":")[0]

        async with aiosqlite.connect(db_path) as db:
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


@domain_event("profile_deleted", extract_delete_data)
async def delete_profile(state_key: str, db_path: str = None) -> bool:
    """Delete user profile permanently."""
    db_path = _get_db_path(db_path)
    await _ensure_schema(db_path)

    try:
        user_id = state_key.split(":")[0]

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
            await db.commit()
            return cursor.rowcount > 0

    except Exception:
        return False
