"""Context assembly - build agent context from domain primitives.

Combines system identity, memory, conversation, and working state into unified context.
Order matters: memory → system → conversation → knowledge → working → execution.
"""

from cogency.context.conversation import build_conversation_context
from cogency.context.knowledge import build_knowledge_context
from cogency.context.memory import build_memory_context
from cogency.context.system import build_system_context
from cogency.context.working import build_working_context


class ContextError(Exception):
    """Context assembly errors."""

    pass


async def build_context(
    conversation=None,
    working_state=None,
    execution=None,
    tools=None,
    memory=None,
    user_id="default",
    query="",
    iteration=1,
) -> str:
    """Context assembly from domain primitives - functional composition."""
    from .execution import build_execution_context

    # Build context in canonical order
    contexts = []

    # Memory first - long-term knowledge base
    if memory:
        contexts.append(await build_memory_context(memory, user_id))

    # System identity - who the agent is
    contexts.append(await build_system_context(iteration=iteration))

    # Current conversation context
    if conversation:
        contexts.append(await build_conversation_context(conversation))

    # Retrieved knowledge for query
    if query:
        contexts.append(await build_knowledge_context(query, user_id))

    # Working state for current task
    if working_state:
        contexts.append(await build_working_context(working_state))

    # Execution context from previous iterations
    if execution:
        contexts.append(await build_execution_context(execution))

    # Available tools
    if tools:
        contexts.append(_build_tools_context(tools))

    return "\n\n".join(filter(None, contexts))


def _build_tools_context(tools) -> str:
    """Build tools context with canonical formatting."""
    if not tools:
        return None
    from cogency.tools.registry import build_tool_schemas

    content = build_tool_schemas(tools)
    return f"AVAILABLE TOOLS:\n{content}" if content else None
