"""Context: Elegant namespace API for user-scoped agent context."""

from .assembly import context
from .conversation import conversation
from .knowledge import knowledge
from .memory import memory
from .system import system
from .working import working

__all__ = [
    # Core context assembly
    "context",
    # 5 Namespaces
    "system",  # system.format()
    "conversation",  # conversation.format(), conversation.get(), conversation.add(), conversation.clear()
    "knowledge",  # knowledge.format(), knowledge.search(), knowledge.store(), knowledge.list()
    "memory",  # memory.format(), memory.get(), memory.update(), memory.clear()
    "working",  # working.format(), working.get(), working.update(), working.clear()
]
