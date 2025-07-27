"""Magical memory interface that auto-configures backends."""

from typing import List

from .backends.base import MemoryBackend


class Memory:
    """Magical memory interface that auto-configures backends."""

    @staticmethod
    def create(backend_name: str = "filesystem", **config) -> MemoryBackend:
        """Auto-magical backend creation."""
        if backend_name == "filesystem":
            from .backends.filesystem import FileBackend

            return FileBackend(**config)
        elif backend_name == "postgres":
            from .backends.postgres import PGVectorBackend

            return PGVectorBackend(**config)
        elif backend_name == "chroma":
            from .backends.chroma import ChromaBackend

            return ChromaBackend(**config)
        elif backend_name == "pinecone":
            from .backends.pinecone import PineconeBackend

            return PineconeBackend(**config)
        else:
            raise ValueError(f"Unknown backend: {backend_name}")

    @staticmethod
    def list_backends() -> List[str]:
        """List available backend names."""
        return ["filesystem", "postgres", "chroma", "pinecone"]
