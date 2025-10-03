"""Context assembly for streaming agents.

Core principle: Rebuild complete context from storage each call rather than
maintaining state in memory. Enables crash recovery, concurrent safety, and
eliminates stale state bugs.

Public API:
- assemble() - Complete context assembly (system + profile + conversation + task)
- learn() - Profile learning from user patterns

Internal modules:
- conversation.* - HISTORY + CURRENT formatting (not exposed)
- profile.* - User pattern learning
- system.* - Core system prompt construction

Agent flow:
- First message: user in DB → HISTORY empty, CURRENT empty → clean start
- Replay: user + partial cycle in DB → HISTORY + CURRENT auto-included
- Always call context.assemble() - it handles everything automatically
"""

from collections.abc import Sequence

from ..core.protocols import Storage, Tool
from .profile import format as profile_format
from .profile import learn
from .system import prompt as system_prompt


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
    from . import conversation

    prompt = [system_prompt(tools=tools, identity=identity, instructions=instructions)]

    if profile_enabled:
        profile_content = await profile_format(user_id, storage)
        if profile_content:
            prompt.append(profile_content)

    conversation_context = await conversation.full_context(
        conversation_id, user_id, storage, history_window
    )
    if conversation_context:
        prompt.append(conversation_context)

    return [{"role": "user", "content": "\n\n".join(prompt)}]


__all__ = ["assemble", "learn"]
