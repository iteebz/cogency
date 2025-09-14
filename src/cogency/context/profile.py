"""User profile management and learning."""

import json

from ..lib.logger import logger
from ..lib.storage import load_profile, save_profile
from .constants import PROFILE_LIMITS

PROFILE_TEMPLATE = """Current: {profile}
Messages: {user_messages}
{instruction}
Example: {{"who":"developer","style":"direct","focus":"AI projects","interests":"tech","misc":"likes cats, morning person"}}"""


def prompt(profile: dict, user_messages: list, compress: bool = False) -> str:
    """Generate profile learning prompt."""
    if compress:
        return PROFILE_TEMPLATE.format(
            profile=json.dumps(profile),
            user_messages="\n".join(user_messages),
            instruction=f"Compress to under {PROFILE_LIMITS['compress_target']} chars. JSON only.",
        )
    return PROFILE_TEMPLATE.format(
        profile=json.dumps(profile),
        user_messages="\n".join(user_messages),
        instruction="Update profile or return SKIP. JSON only.",
    )


async def get(user_id: str) -> dict | None:
    """Get latest user profile."""
    if not user_id or user_id == "default":
        return None
    try:
        return await load_profile(user_id)
    except Exception as e:
        logger.debug(f"⚠️ Profile fetch failed for {user_id}: {e}")
        return None


async def format(user_id: str) -> str:
    """Format user profile for context display."""
    try:
        profile_data = await get(user_id)
        if not profile_data:
            return ""

        return f"USER PROFILE:\n{json.dumps(profile_data, indent=2)}"
    except Exception as e:
        logger.debug(f"⚠️ Profile format failed for {user_id}: {e}")
        return ""


async def should_learn(user_id: str) -> bool:
    """Check if 5+ new user messages since last learning."""
    current = await get(user_id)
    if not current:
        return False

    import sqlite3

    from ..lib.storage import Paths

    last_learned = current.get("_meta", {}).get("last_learned_at", 0)

    current_chars = len(json.dumps(current))
    if current_chars > PROFILE_LIMITS["compress_threshold"]:
        logger.debug(
            f"🚨 EMERGENCY: {current_chars} chars > {PROFILE_LIMITS['compress_threshold']}"
        )
        return True

    db_path = Paths.db()
    if not db_path.exists():
        return False

    with sqlite3.connect(db_path) as db:
        unlearned = db.execute(
            """
                SELECT COUNT(*) FROM conversations
                WHERE user_id = ? AND type = 'user' AND timestamp > ?
            """,
            (user_id, last_learned),
        ).fetchone()[0]
    if unlearned >= PROFILE_LIMITS["learning_trigger"]:
        logger.debug(
            f"📊 DELTA: {unlearned} new USER messages >= {PROFILE_LIMITS['learning_trigger']}"
        )
        return True

    return False


def learn(user_id: str, llm):
    """Profile learning - handles everything internally (non-blocking)."""
    if not user_id or user_id == "default" or not llm:
        return

    # Skip learning entirely during tests to prevent warnings
    import os

    if "pytest" in os.environ.get("_", "") or "PYTEST_CURRENT_TEST" in os.environ:
        logger.debug(f"🧠 Profile learning skipped in test environment for {user_id}")
        return

    # Note: should_learn is now async, but this is sync context for fire-and-forget
    # Just trigger learning and let learn_async do the check internally

    # Background execution (non-blocking)
    import asyncio

    # Fire-and-forget background learning
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(learn_async(user_id, llm))

        # Prevent "task not awaited" warning by adding done callback that handles exceptions
        def handle_task_done(task):
            import contextlib

            with contextlib.suppress(Exception):
                task.result()  # This will raise any exception that occurred

        task.add_done_callback(handle_task_done)
    except RuntimeError:
        # No event loop (e.g., in tests) - skip background learning
        pass
    logger.debug(f"🧠 Profile learning triggered for {user_id}")


async def learn_async(user_id: str, llm) -> bool:
    """Internal async learning implementation."""

    # Check if learning is needed
    if not await should_learn(user_id):
        return False

    current = await get(user_id) or {
        "who": "",
        "style": "",
        "focus": "",
        "interests": "",
        "misc": "",
        "_meta": {},
    }
    last_learned = current.get("_meta", {}).get("last_learned_at", 0)

    # Get unlearned messages
    import sqlite3
    import time

    from ..lib.storage import Paths

    db_path = Paths.db()
    if not db_path.exists():
        return False

    with sqlite3.connect(db_path) as db:
        # Get ONLY user messages for profile learning
        messages = db.execute(
            """
                SELECT content, timestamp FROM conversations
                WHERE user_id = ? AND type = 'user' AND timestamp > ?
                ORDER BY timestamp ASC
                LIMIT ?
            """,
            (user_id, last_learned, PROFILE_LIMITS["learning_window"]),
        ).fetchall()

    if not messages:
        return False

    # Create learning prompt from message batch
    message_texts = [msg[0] for msg in messages]

    logger.debug(f"🧠 LEARNING: {len(messages)} new messages for {user_id}")

    # Check if compression needed
    current_chars = len(json.dumps(current))
    compress = current_chars > PROFILE_LIMITS["compress_threshold"]
    updated = await update_profile(current, message_texts, llm, compress=compress)

    if updated and updated != current:
        # Embed metadata in profile
        updated["_meta"] = {
            "last_learned_at": time.time(),
            "messages_processed": len(messages),
        }
        try:
            await save_profile(user_id, updated)
            final_chars = len(json.dumps(updated))
            logger.debug(f"💾 DELTA SAVE: ✅ {final_chars} chars")
            return True
        except Exception as e:
            final_chars = len(json.dumps(updated))
            logger.debug(f"💾 DELTA SAVE: ❌ {final_chars} chars - {e}")
            return False

    return False


async def update_profile(
    current: dict, user_messages: list, llm, compress: bool = False
) -> dict | None:
    """Process profile update or compression."""
    prompt_text = prompt(current, user_messages, compress=compress)

    messages = [{"role": "user", "content": prompt_text}]
    result = await llm.generate(messages)

    if not result:
        return current if compress else None

    # Strip markdown blocks and parse JSON
    clean_result = result.strip()
    if clean_result.startswith("```json"):
        clean_result = clean_result[7:]
    if clean_result.startswith("```"):
        clean_result = clean_result[3:]
    if clean_result.endswith("```"):
        clean_result = clean_result[:-3]

    try:
        parsed = json.loads(clean_result.strip())
        if compress:
            current_chars = len(json.dumps(current))
            compressed_chars = len(json.dumps(parsed))
            logger.debug(f"🗜️ COMPRESSED: {current_chars} → {compressed_chars} chars")
            return parsed
        if result.strip().upper() != "SKIP":
            return parsed
    except json.JSONDecodeError:
        error_type = "COMPRESS" if compress else "JSON PARSE"
        logger.debug(f"🚨 {error_type} ERROR: {result[:100]}...")

    return current if compress else None


__all__ = ["get", "format", "learn"]
