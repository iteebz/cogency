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
    query: str,
    user_id: str,
    conversation_id: str,
    *,
    tools: Sequence[Tool],
    storage: Storage,
    history_window: int,
    profile_enabled: bool,
) -> list[dict]:
    """Assemble complete context: system prompt + conversation context + user query."""
    from . import conversation

    # Build system sections
    system_sections = [system_prompt(tools)]

    # Add user profile if available
    if profile_enabled:
        profile_content = await profile_format(user_id, storage)
        if profile_content:
            system_sections.append(profile_content)

    # Add conversation context (HISTORY + CURRENT) if any exists
    conversation_context = await conversation.full_context(conversation_id, storage, history_window)
    if conversation_context:
        system_sections.append(conversation_context)

    # Task boundary
    system_sections.append(
        "CURRENT TASK: Execute the following request independently. "
        "Previous responses are context only - do not assume prior completion."
    )

    return [
        {"role": "system", "content": "\n\n".join(system_sections)},
        {"role": "user", "content": query},
    ]


__all__ = ["assemble", "learn"]
