"""Context: Elegant namespace API for user-scoped agent context."""

from .assembly import context
from .conversation import conversation
from .knowledge import knowledge
from .memory import memory
from .persistence import persist, profile
from .system import system
from .working import working

__all__ = [
    # Core context assembly
    "context",
    "system",
    "persist",
    "profile",
    # Elegant namespace API
    "conversation",  # conversation.format(), conversation.get(), conversation.add(), conversation.clear()
    "knowledge",  # knowledge.format(), knowledge.search(), knowledge.store(), knowledge.list()
    "memory",  # memory.format(), memory.get(), memory.update(), memory.set_preference()
    "working",  # working.format(), working.get(), working.update(), working.clear()
]
