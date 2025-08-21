"""Assembly: Context orchestrator - combines all sources."""

from .conversation import conversation
from .memory import memory as memory_system
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
        iteration: int = 1,
        memory: bool = True,
    ) -> list:
        """Assemble unified context as canonical message format."""
        if user_id is None:
            raise ValueError("user_id cannot be None")

        messages = []

        # All iterations: System message with XML format instructions
        # Iteration 1: Include security evaluation, others: exclude security
        include_security = iteration == 1
        messages.append(
            {
                "role": "system",
                "content": system.format(tools=tools, include_security=include_security),
            }
        )

        # Iteration 1: Add conversation history + user context
        if iteration == 1:
            # Add conversation history as structured messages
            message_history = conversation.messages(conversation_id)
            if message_history:
                messages.extend(message_history)

            # Add current query context (skip user memory if disabled)
            context_parts = []
            if memory:
                context_parts.append(memory_system.format(user_id))

            context_content = "\n\n".join(filter(None, context_parts))

            if context_content:
                messages.append({"role": "user", "content": context_content})

        # All iterations: working memory + current query
        working_context = working.format(task_id)
        if working_context:
            messages.append({"role": "user", "content": working_context})
        messages.append({"role": "user", "content": query})

        return messages


# Singleton instance
context = Context()
