"""Memory subdomain - user profile and learning systems."""

from typing import Any, Optional

from .learn import learn
from .memory import Memory, Profile
from .recall import Recall


async def build_memory_context(memory: Any, user_id: str) -> Optional[str]:
    """Build memory context - canonical domain function.

    Args:
        memory: Memory component instance
        user_id: User identifier for profile retrieval

    Returns:
        Profile context string or None
    """
    if not memory:
        return None

    try:
        profile_context = await memory.activate(user_id)
        return profile_context if profile_context else None

    except Exception as e:
        from cogency.events import emit

        emit("context", domain="memory", status="error", error=str(e))
        return None


__all__ = ["build_memory_context", "Memory", "Profile", "learn", "Recall"]
