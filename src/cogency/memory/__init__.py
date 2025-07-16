"""Memory primitives for Cogency agents."""
from .base import BaseMemory, MemoryArtifact, MemoryType, SearchType
from .filesystem import FSMemory
from .memorize import memorize_node

# Vector backends - imported lazily to avoid hard dependencies
try:
    from .pinecone import PineconeMemory
    _PINECONE_AVAILABLE = True
except ImportError:
    _PINECONE_AVAILABLE = False

try:
    from .chromadb import ChromaDBMemory
    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False

try:
    from .pgvector import PGVectorMemory
    _PGVECTOR_AVAILABLE = True
except ImportError:
    _PGVECTOR_AVAILABLE = False

# Base exports
__all__ = ["BaseMemory", "MemoryArtifact", "MemoryType", "SearchType", "FSMemory", "memorize_node"]

# Add vector backends to exports if available
if _PINECONE_AVAILABLE:
    __all__.append("PineconeMemory")
if _CHROMADB_AVAILABLE:
    __all__.append("ChromaDBMemory")
if _PGVECTOR_AVAILABLE:
    __all__.append("PGVectorMemory")


def get_available_backends():
    """Get list of available memory backends."""
    backends = ["FSMemory"]
    if _PINECONE_AVAILABLE:
        backends.append("PineconeMemory")
    if _CHROMADB_AVAILABLE:
        backends.append("ChromaDBMemory")
    if _PGVECTOR_AVAILABLE:
        backends.append("PGVectorMemory")
    return backends