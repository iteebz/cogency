"""Magical memory interface that auto-configures backends."""

from typing import List

from .core import MemoryBackend


class Memory:
    """Magical memory interface that auto-configures backends."""

    @staticmethod
    def create(backend_name: str = "filesystem", **config) -> MemoryBackend:
        """Auto-magical backend creation."""
        from .backends import get_backend

        backend_class = get_backend(backend_name)
        return backend_class(**config)

    @staticmethod
    def list_backends() -> List[str]:
        """List available backend names."""
        from .backends import list_backends

        return list_backends()
