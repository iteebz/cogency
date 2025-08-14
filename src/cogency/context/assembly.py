"""Context assembly - canonical cross-domain context building.

Historical discovery: Memory first, tools last, double newline separation.
Agent assembles context, not State - context cuts across domains.
"""

from typing import Any, Optional

from cogency.context.conversation import ConversationContext
from cogency.context.knowledge import KnowledgeContext
from cogency.context.memory import MemoryContext
from cogency.context.system import SystemContext
from cogency.context.working import WorkingContext


class ContextError(Exception):
    """Context assembly errors."""
    pass


async def build_context(
    conversation: Any = None,
    working_state: Any = None,
    execution: Any = None,
    tools: list[Any] = None,
    memory: Optional[Any] = None,
    user_id: str = "default",
    query: str = "",
    iteration: int = 1
) -> str:
    """Context assembly from domain primitives.
    
    Builds context directly from domain objects without State container.
    Historical discovery from 2025-08-04 design logs:
    - Memory first - stable user frame for LLM interpretation
    - Tools last - actionable options, not situational facts  
    - Double newline separation - clean visual boundaries
    
    Args:
        conversation: Conversation domain object
        working_state: WorkingState domain object  
        execution: Execution domain object
        tools: Available tool instances
        memory: Memory component (optional)
        user_id: User identifier for memory context
        query: Current query for knowledge context
        iteration: Current reasoning iteration
        
    Returns:
        Natural language context string for LLM reasoning
    """
    parts = []
    
    # Memory domain - Profile injection FIRST
    if memory:
        memory_context = MemoryContext(memory, user_id)
        memory_content = await memory_context.build()
        if memory_content:
            parts.append(memory_content)
    
    # System domain - Identity and security context
    system_context = SystemContext(iteration=iteration)
    system_content = await system_context.build()
    if system_content:
        parts.append(system_content)
        
    # Conversation domain - Message history
    if conversation:
        conversation_context = ConversationContext(conversation)
        conversation_content = await conversation_context.build() 
        if conversation_content:
            parts.append(conversation_content)
        
    # Knowledge domain - Automatic retrieval
    if query:
        knowledge_context = KnowledgeContext(query, user_id)
        knowledge_content = await knowledge_context.build()
        if knowledge_content:
            parts.append(knowledge_content)
    
    # Working domain - Task-scoped state
    if working_state:
        working_context = WorkingContext(working_state)
        working_content = await working_context.build()
        if working_content:
            parts.append(working_content)
    
    # Execution domain - Tool history
    if execution:
        from .execution import ExecutionContext
        execution_context = ExecutionContext(execution)
        execution_content = await execution_context.build()
        if execution_content:
            parts.append(execution_content)
        
    # Tools domain - Registry LAST
    if tools:
        tool_content = _build_tool_registry(tools)
        if tool_content:
            parts.append(f"AVAILABLE TOOLS:\n{tool_content}")
    
    # Assembly: double newline separation, no adornments
    return "\n\n".join(parts) if parts else ""


def _build_tool_registry(tools) -> str:
    """Build complete tool registry for LLM - preserved from legacy."""
    if not tools:
        return "No tools available."

    descriptions = []
    for tool in tools:
        descriptions.append(f"- {tool.name}: {tool.description}")
        descriptions.append(f"  Schema: {getattr(tool, 'schema', 'No schema')}")

        for example in getattr(tool, "examples", []):
            descriptions.append(f"  Example: {example}")

        for rule in getattr(tool, "rules", []):
            descriptions.append(f"  Rule: {rule}")

    return "\n".join(descriptions)