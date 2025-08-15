"""Assembly: Context orchestrator - combines all sources."""

from .conversation import conversation
from .knowledge import knowledge
from .memory import memory
from .system import system
from .working import working


def context(query: str, user_id: str, tools: list = None, tool_results: list = None) -> list[dict]:
    """Assemble complete context including user query."""
    messages = []

    system_content = system(tools)
    context_parts = [
        knowledge(query, user_id),
        memory(user_id),
        working(tool_results),
    ]

    context_content = "\n\n".join(filter(None, context_parts))
    if context_content:
        system_content += f"\n\n{context_content}"

    messages.append({"role": "system", "content": system_content})

    conv_messages = conversation(user_id)
    if conv_messages:
        messages.extend(conv_messages)

    # Include user query in context assembly
    messages.append({"role": "user", "content": query})

    return messages
