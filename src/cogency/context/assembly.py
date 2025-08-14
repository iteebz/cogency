"""Assembly: Context orchestrator - combines all sources."""

from .conversation import conversation
from .knowledge import knowledge
from .memory import memory
from .system import system
from .working import working


def context(query: str, user_id: str, tools: list = None) -> str:
    """Assemble context for query."""
    contexts = [
        system(),
        conversation(user_id),
        knowledge(query, user_id),
        memory(user_id),
        working(tools),
    ]
    return "\n\n".join(filter(None, contexts))
