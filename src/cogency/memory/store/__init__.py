"""Memory services - automagical discovery."""

from typing import Optional, Type

from cogency.utils import Provider

from .base import Store, setup_memory
from .chroma import Chroma
from .filesystem import Filesystem
from .pinecone import Pinecone
from .postgres import PGVector

# Provider registry
_memory_provider = Provider(
    {
        "chroma": Chroma,
        "filesystem": Filesystem,
        "pinecone": Pinecone,
        "postgres": PGVector,
    },
    default="filesystem",
)


def get_store(provider: Optional[str] = None) -> Type[Store]:
    """Get memory store with automagical discovery."""
    return _memory_provider.get(provider)


__all__ = ["Store", "get_store", "setup_memory", "Chroma", "Filesystem", "Pinecone", "PGVector"]
