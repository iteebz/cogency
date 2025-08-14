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
    state: Any, 
    tools: list[Any], 
    memory: Optional[Any], 
    iteration: int = 1
) -> str:
    """Canonical context assembly pattern.
    
    Historical discovery from 2025-08-04 design logs:
    - Memory first - stable user frame for LLM interpretation
    - Tools last - actionable options, not situational facts  
    - Double newline separation - clean visual boundaries
    - Agent assembles, not State - context cuts across domains
    
    Args:
        state: Current agent state (legacy compatibility)
        tools: Available tool instances
        memory: Memory component (optional)
        iteration: Current reasoning iteration
        
    Returns:
        Natural language context string for LLM reasoning
    """
    parts = []
    
    # Memory domain - Profile injection FIRST
    if memory:
        memory_context = MemoryContext(memory, state.user_id)
        memory_content = await memory_context.build()
        if memory_content:
            parts.append(memory_content)
    
    # System domain - Identity and security context
    system_context = SystemContext(iteration=iteration)
    system_content = await system_context.build()
    if system_content:
        parts.append(system_content)
        
    # Conversation domain - Message history
    conversation_context = ConversationContext(state)
    conversation_content = await conversation_context.build() 
    if conversation_content:
        parts.append(conversation_content)
        
    # Knowledge domain - Automatic retrieval
    knowledge_context = KnowledgeContext(state.query, state.user_id)
    knowledge_content = await knowledge_context.build()
    if knowledge_content:
        parts.append(knowledge_content)
    
    # Working domain - Task-scoped workspace
    working_context = WorkingContext(state)
    working_content = await working_context.build()
    if working_content:
        parts.append(working_content)
        
    # Tools domain - Registry LAST
    tool_content = _build_tool_registry(tools)
    if tool_content:
        parts.append(f"AVAILABLE TOOLS:\n{tool_content}")
    
    # Canonical assembly: double newline separation, no adornments
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