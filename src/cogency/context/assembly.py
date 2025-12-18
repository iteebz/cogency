import logging
from collections.abc import Sequence
from typing import Any

from cogency.core.errors import StorageError
from cogency.core.protocols import HistoryTransform, Storage, Tool

from .conversation import to_messages
from .profile import format as profile_format
from .system import prompt as system_prompt

logger = logging.getLogger(__name__)

# 10k events ~2-5MB context, 50-200ms SQLite query, rarely exceeds 128k token limits.
# Conversations beyond this require history_window for bounded memory.
MAX_CONVERSATION_LENGTH = 10000


async def assemble(
    user_id: str,
    conversation_id: str,
    *,
    tools: Sequence[Tool],
    storage: Storage,
    history_window: int | None,
    history_transform: HistoryTransform | None,
    profile_enabled: bool,
    identity: str | None = None,
    instructions: str | None = None,
) -> list[dict[str, Any]]:
    system_content = [
        system_prompt(tools=list(tools), identity=identity, instructions=instructions)
    ]

    if profile_enabled:
        try:
            profile_content = await profile_format(user_id, storage)
        except Exception as exc:
            logger.exception(
                "Context assembly failed to build profile for user=%s: %s", user_id, exc
            )
            raise
        if profile_content:
            system_content.append(profile_content)

    messages: list[dict[str, Any]] = []

    try:
        load_limit = None
        if history_window is not None:
            load_limit = history_window * 2
        events = await storage.load_messages(conversation_id, user_id, limit=load_limit)

        if history_window is None and len(events) > MAX_CONVERSATION_LENGTH:
            raise StorageError(
                f"Conversation exceeds {MAX_CONVERSATION_LENGTH} events. "
                f"Enable history_window to limit context size.",
                retryable=False,
            )
    except Exception as exc:
        logger.exception(
            "Context assembly failed loading messages for conversation=%s user=%s: %s",
            conversation_id,
            user_id,
            exc,
        )
        raise
    if events:
        conv_messages = to_messages(events)
        if history_window is not None:
            conv_messages = conv_messages[-history_window:]
        if history_transform:
            conv_messages = await history_transform(conv_messages)
        messages.extend(conv_messages)

    return [{"role": "system", "content": "\n\n".join(system_content)}, *messages]
