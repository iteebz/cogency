"""Assembly: Context orchestrator - combines all sources."""

from .conversation import conversation
from .knowledge import knowledge
from .memory import memory
from .system import system
from .working import working


def inject_context(query: str, user_id: str, tool_results: list = None) -> str:
    """Inject relevant context for query - pure function."""
    contexts = [
        system(),
        conversation(user_id),
        knowledge(query, user_id),
        memory(user_id),
        working(tool_results),
    ]
    return "\n\n".join(filter(None, contexts))
