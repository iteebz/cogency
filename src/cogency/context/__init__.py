"""Context assembly for streaming agents.

Core principle: Rebuild complete context from storage each call rather than
maintaining state in memory. Enables crash recovery, concurrent safety, and
eliminates stale state bugs.

Public API:
- assemble() - Complete context assembly (system + profile + conversation + task)
- learn() - Profile learning from user patterns

Internal modules:
- conversation.* - Event to message conversion
- profile.* - User pattern learning
- system.* - Core system prompt construction

Agent flow:
- First message: user in DB → HISTORY empty, CURRENT empty → clean start
- Replay: user + partial cycle in DB → HISTORY + CURRENT auto-included
- Always call context.assemble() - it handles everything automatically
"""

from .assembly import assemble
from .profile import learn, wait_for_background_tasks

__all__ = ["assemble", "learn", "wait_for_background_tasks"]
