"""Context architecture - organized assembly, natural delivery.

Replaces the broken 31-field state complexity with organized context namespaces.
Each namespace curates relevant information; final assembly collapses to natural
language context for LLM reasoning.

Constitutional principle: Natural language context for LLM, organized assembly for developers.
"""

from cogency.context.assembly import ContextError, build_context
from cogency.context.conversation import build_conversation_context
from cogency.context.knowledge import build_knowledge_context
from cogency.context.memory import build_memory_context
from cogency.context.system import build_system_context
from cogency.context.working import build_working_context

__all__ = [
    "build_context",
    "ContextError",
    "build_conversation_context",
    "build_knowledge_context",
    "build_memory_context",
    "build_system_context",
    "build_working_context",
]
