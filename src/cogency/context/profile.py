"""User profile management and learning."""

import json
from typing import Optional

from ..lib.logger import logger
from ..lib.storage import load_profile, save_profile
from .constants import PROFILE_LIMITS

# =============================================================================
# PROFILE LEARNING SYSTEM
# =============================================================================

PROFILE_TEMPLATE = """Current: {profile}
Messages: {user_messages}
{instruction}
Example: {{"who":"developer","style":"direct","focus":"AI projects","interests":"tech","misc":"likes cats, morning person"}}"""


def prompt(profile: dict, user_messages: list, compress: bool = False) -> str:
    """Generate profile learning prompt."""
    if compress:
        len(json.dumps(profile))
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


def get(user_id: str) -> Optional[dict]:
    """Get latest user profile."""
    if not user_id or user_id == "default":
        return None
    try:
        return load_profile(user_id)
    except Exception as e:
        logger.debug(f"⚠️ Profile fetch failed for {user_id}: {e}")
        return None


def format(user_id: str) -> str:
    """Format user profile for context display."""
    try:
        profile_data = get(user_id)
        if not profile_data:
            return ""

        return f"USER PROFILE:\n{json.dumps(profile_data, indent=2)}"
    except Exception as e:
        logger.debug(f"⚠️ Profile format failed for {user_id}: {e}")
        return ""


def _delta(user_id: str) -> bool:
    """Check if 5+ new user messages since last learning."""
    current = get(user_id)
    if not current:
        return False

    import sqlite3

    from ..lib.storage import get_db_path

    # Get metadata from embedded profile
    last_learned = current.get("_meta", {}).get("last_learned_at", 0)

    # Emergency: Profile over compression threshold
    current_chars = len(json.dumps(current))
    if current_chars > PROFILE_LIMITS["compress_threshold"]:
        logger.debug(
            f"🚨 EMERGENCY: {current_chars} chars > {PROFILE_LIMITS['compress_threshold']}"
        )
        return True

    # Count unlearned messages
    db_path = get_db_path()
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

    # Trigger: 5+ new USER messages only
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

    # Check if learning needed (internal responsibility)
    if not _delta(user_id):
        return

    # Background execution (non-blocking)
    import asyncio

    # Fire-and-forget background learning
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_learn(user_id, llm))

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


async def _learn(user_id: str, llm) -> bool:
    """Internal async learning implementation."""

    current = get(user_id) or {
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

    from ..lib.storage import get_db_path

    db_path = get_db_path()
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
    updated = await _process_profile(current, message_texts, llm, compress=compress)

    if updated and updated != current:
        # Embed metadata in profile
        updated["_meta"] = {
            "last_learned_at": time.time(),
            "messages_processed": len(messages),
        }
        success = save_profile(user_id, updated)

        final_chars = len(json.dumps(updated))
        logger.debug(f"💾 DELTA SAVE: {'✅' if success else '❌'} {final_chars} chars")
        return success

    return False


async def _process_profile(
    current: dict, user_messages: list, llm, compress: bool = False
) -> Optional[dict]:
    """Process profile update or compression."""
    prompt_text = prompt(current, user_messages, compress=compress)

    messages = [{"role": "user", "content": prompt_text}]
    result = await llm.generate(messages)

    if not result.success:
        logger.debug(f"🚨 GENERATE ERROR: {result.error}")
        return None

    result = result.unwrap()

    if compress:
        if result:
            try:
                compressed = _clean_json(result)
                current_chars = len(json.dumps(current))
                compressed_chars = len(json.dumps(compressed))
                logger.debug(f"🗜️ COMPRESSED: {current_chars} → {compressed_chars} chars")
                return compressed
            except json.JSONDecodeError:
                logger.debug(f"🚨 COMPRESS JSON ERROR: {result[:100]}...")
        return current
    if result and result.strip().upper() != "SKIP":
        try:
            return _clean_json(result)
        except json.JSONDecodeError:
            logger.debug(f"🚨 JSON PARSE ERROR: {result[:100]}...")
    return None


def _clean_json(result: str) -> dict:
    """Strip markdown blocks and parse JSON."""
    clean_result = result.strip()
    if clean_result.startswith("```json"):
        clean_result = clean_result[7:]
    if clean_result.startswith("```"):
        clean_result = clean_result[3:]
    if clean_result.endswith("```"):
        clean_result = clean_result[:-3]

    return json.loads(clean_result.strip())


# Direct function exports - no ceremony
__all__ = ["get", "format", "learn"]
