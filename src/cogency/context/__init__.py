"""Context architecture - organized assembly, natural delivery.

Replaces the broken 31-field state complexity with organized context namespaces.
Each namespace curates relevant information; final assembly collapses to natural
language context for LLM reasoning.

Constitutional principle: Natural language context for LLM, organized assembly for developers.
"""

from cogency.context.assembly import build_context, ContextError
from cogency.context.conversation import ConversationContext
from cogency.context.knowledge import KnowledgeContext  
from cogency.context.memory import MemoryContext
from cogency.context.system import SystemContext
from cogency.context.working import WorkingContext

__all__ = [
    "build_context", 
    "ContextError",
    "ConversationContext",
    "KnowledgeContext", 
    "MemoryContext",
    "SystemContext",
    "WorkingContext"
]