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
        tool_results: list = None,
        tools: dict = None,
        iteration: int = 0,
    ) -> str:
        """Assemble unified context for query using elegant namespace API."""
        if user_id is None:
            raise ValueError("user_id cannot be None")

        contexts = [
            system(tools=tools, iteration=iteration),
            conversation.format(user_id),
            knowledge.format(query, user_id),
            memory.format(user_id),
            working.format(tool_results),
            f"TASK: {query}",
        ]
        return "\n\n".join(filter(None, contexts))


# Singleton instance
context = Context()
