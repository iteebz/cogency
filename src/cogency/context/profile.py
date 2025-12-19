"""User profiles: LLM-learned JSON, not embeddings.

Why no embeddings?
- Transparency: readable JSON, not opaque vectors
- Simplicity: no vector DB infrastructure
- Privacy: deletable, auditable format

Triggers: every 5 messages or size > 2000 chars (compaction).
"""

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING, Any

from cogency.core.protocols import parse_profile_dict

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from cogency.core.protocols import LLM, Storage

DEFAULT_CADENCE = 5
COMPACT_THRESHOLD = 2000

PROFILE_TEMPLATE = """Current: {profile}
Messages: {user_messages}
{instruction}
Example: {{"who":"developer","style":"direct","focus":"AI projects","interests":"tech","misc":"likes cats, morning person"}}"""


def prompt(profile: dict[str, Any], user_messages: list[str], compact: bool = False) -> str:
    """Generate profile learning prompt."""
    if compact:
        return PROFILE_TEMPLATE.format(
            profile=json.dumps(profile),
            user_messages="\n".join(user_messages),
            instruction="Profile too large. Compact to essential facts only. JSON only.",
        )
    return PROFILE_TEMPLATE.format(
        profile=json.dumps(profile),
        user_messages="\n".join(user_messages),
        instruction="Update profile keeping it concise. Return SKIP if no changes needed. JSON only.",
    )


async def get(user_id: str | None, storage: "Storage | None" = None) -> dict[str, Any] | None:
    if not user_id:
        return None
    if storage is None:
        from cogency.lib.sqlite import default_storage

        storage = default_storage()
    try:
        return await storage.load_profile(user_id)
    except Exception as e:
        if "unable to open database file" in str(e):
            return {}
        raise RuntimeError(f"Profile fetch failed for {user_id}: {e}") from e


async def format(user_id: str | None, storage: "Storage | None" = None) -> str:
    try:
        profile_data = await get(user_id, storage)
        if not profile_data:
            return ""

        return f"USER PROFILE:\n{json.dumps(profile_data, indent=2)}"
    except Exception as e:
        raise RuntimeError(f"Profile format failed for {user_id}: {e}") from e


async def _should_learn_with_profile(
    user_id: str,
    current: dict[str, Any] | None,
    *,
    storage: "Storage",
    cadence: int = DEFAULT_CADENCE,
) -> bool:
    if not current:
        unlearned = await storage.count_user_messages(user_id, 0)
        if unlearned >= cadence:
            logger.debug(f"📊 INITIAL LEARNING: {unlearned} messages for {user_id}")
            return True
        return False

    current_chars = len(json.dumps(current))
    if current_chars > COMPACT_THRESHOLD:
        logger.debug(f"🚨 COMPACT: {current_chars} chars")
        return True

    last_learned = current.get("_meta", {}).get("last_learned_at", 0)
    unlearned = await storage.count_user_messages(user_id, last_learned)

    if unlearned >= cadence:
        logger.debug(f"📊 LEARNING: {unlearned} new messages")
        return True

    return False


async def should_learn(
    user_id: str,
    *,
    storage: "Storage",
    cadence: int = DEFAULT_CADENCE,
) -> bool:
    current = await get(user_id, storage)
    return await _should_learn_with_profile(user_id, current, storage=storage, cadence=cadence)


_background_tasks: set[asyncio.Task[Any]] = set()


def _task_done_callback(task: asyncio.Task[Any]) -> None:
    _background_tasks.discard(task)
    if task.cancelled():
        return
    if exc := task.exception():
        logger.warning(f"Background profile learning failed: {exc}")


async def wait_for_background_tasks(timeout: float = 10.0) -> None:
    """Wait for pending profile learning tasks to complete."""
    if not _background_tasks:
        return
    tasks = list(_background_tasks)
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
    except TimeoutError:
        logger.warning(f"Timeout waiting for {len(tasks)} background profile tasks")


def learn(
    user_id: str | None,
    *,
    profile_enabled: bool,
    storage: "Storage",
    llm: "LLM",
    cadence: int = DEFAULT_CADENCE,
):
    if not profile_enabled or not user_id or not llm:
        return

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(
            learn_async(
                user_id,
                storage=storage,
                llm=llm,
                cadence=cadence,
            )
        )
        _background_tasks.add(task)
        task.add_done_callback(_task_done_callback)
    except RuntimeError:
        pass


async def learn_async(
    user_id: str,
    *,
    storage: "Storage",
    llm: "LLM",
    cadence: int = DEFAULT_CADENCE,
) -> bool:
    current = await get(user_id, storage) or {
        "who": "",
        "style": "",
        "focus": "",
        "interests": "",
        "misc": "",
        "_meta": {},
    }
    last_learned = current.get("_meta", {}).get("last_learned_at", 0)

    if not await _should_learn_with_profile(user_id, current, storage=storage, cadence=cadence):
        return False

    limit = cadence * 2

    message_texts = await storage.load_user_messages(user_id, last_learned, limit)

    if not message_texts:
        return False

    logger.debug(f"🧠 LEARNING: {len(message_texts)} new messages for {user_id}")

    # Check size and update
    compact = len(json.dumps(current)) > COMPACT_THRESHOLD
    updated = await update_profile(current, message_texts, llm, compact=compact)

    if updated and updated != current:
        updated["_meta"] = {
            "last_learned_at": time.time(),
            "messages_processed": len(message_texts),
        }
        await storage.save_profile(user_id, updated)
        logger.debug(f"💾 SAVED: {len(json.dumps(updated))} chars")
        return True

    return False


async def update_profile(
    current: dict[str, Any], user_messages: list[str], llm: "LLM", compact: bool = False
) -> dict[str, Any] | None:
    """Update or compact profile."""
    prompt_text = prompt(current, user_messages, compact=compact)
    result = await llm.generate([{"role": "user", "content": prompt_text}])

    if not result:
        return current if compact else None

    # Parse JSON (strip common markdown)
    clean = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```")

    try:
        raw: object = json.loads(clean)
        parsed = parse_profile_dict(raw)
        if compact or result.strip().upper() != "SKIP":
            return dict(parsed)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse error during profile update: {result[:50]}...") from e
    except Exception as e:
        raise RuntimeError(f"Invalid profile format: {e}") from e

    return current if compact else None


__all__ = ["format", "get", "learn"]
