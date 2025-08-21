"""Context: Elegant namespace API for user-scoped agent context."""

from .assembly import context
from .conversation import conversation
from .memory import memory
from .system import system
from .working import working

__all__ = [
    # Core context assembly
    "context",
    # 3 Namespaces
    "system",  # system.format()
    "conversation",  # conversation.format(), get(), add(), clear()
    "memory",  # memory.format(), memory.get(), memory.update(), memory.clear()
    "working",  # working.format(), working.get(), working.update(), working.clear()
]
