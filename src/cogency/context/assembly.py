"""Assembly: Context orchestrator - combines all sources."""

from .conversation import conversation
from .knowledge import knowledge
from .memory import memory
from .system import system
from .working import working


class Context:
    """Unified context assembly with user-scoped data integration."""

    def assemble(
        self,
        query: str,
        user_id: str,
        conversation_id: str,
        task_id: str,
        tools: dict = None,
    ) -> str:
        """Assemble unified context for query using elegant namespace API."""
        if user_id is None:
            raise ValueError("user_id cannot be None")

        contexts = [
            system.format(tools=tools),
            conversation.format(conversation_id),
            knowledge.format(user_id),
            memory.format(user_id),
            working.format(task_id),
            f"TASK: {query}",
        ]
        return "\n\n".join(filter(None, contexts))


# Singleton instance
context = Context()
