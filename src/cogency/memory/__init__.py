"""Memory primitives for Cogency agents."""

from .search import search
from .types import Memory, MemoryType, SearchType


# Defer store imports to avoid circular dependency during module loading
def __getattr__(name):
    if name in ("Store", "setup_memory", "Chroma", "Filesystem", "PGVector", "Pinecone"):
        from .store import Chroma, Filesystem, PGVector, Pinecone, Store, setup_memory

        globals().update(
            {
                "Store": Store,
                "setup_memory": setup_memory,
                "Chroma": Chroma,
                "Filesystem": Filesystem,
                "PGVector": PGVector,
                "Pinecone": Pinecone,
            }
        )
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "Memory",
    "MemoryType",
    "SearchType",
    "setup_memory",
    "Store",
    "Chroma",
    "Filesystem",
    "Pinecone",
    "PGVector",
    "search",
]
