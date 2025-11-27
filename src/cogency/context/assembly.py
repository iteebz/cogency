import logging
from collections.abc import Sequence

from ..core.protocols import Storage, Tool
from .conversation import to_messages
from .profile import format as profile_format
from .system import prompt as system_prompt

logger = logging.getLogger(__name__)


async def assemble(
    user_id: str,
    conversation_id: str,
    *,
    tools: Sequence[Tool],
    storage: Storage,
    history_window: int | None,
    profile_enabled: bool,
    identity: str | None = None,
    instructions: str | None = None,
) -> list[dict]:
    """Assemble complete context from storage."""
    system_content = [system_prompt(tools=tools, identity=identity, instructions=instructions)]

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

    messages = []

    try:
        load_limit = None
        if history_window is not None:
            # 2x: ensures complete turns (think+respond pairs)
            load_limit = history_window * 2
        events = await storage.load_messages(conversation_id, user_id, limit=load_limit)
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
        messages.extend(conv_messages)

    return [{"role": "system", "content": "\n\n".join(system_content)}] + messages
