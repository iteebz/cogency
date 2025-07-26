"""Magical memory interface that auto-configures backends."""

from typing import List

from .core import MemoryBackend


class Memory:
    """Magical memory interface that auto-configures backends."""

    @staticmethod
    def create(backend_name: str = "filesystem", **config) -> MemoryBackend:
        """Auto-magical backend creation."""
        from cogency.services import memory

        backend_class = memory(backend_name)
        return backend_class(**config)

    @staticmethod
    def list_backends() -> List[str]:
        """List available backend names."""

        # Get all available memory backends from service registry
        from cogency.services import _registry

        _registry._discover_services()
        return list(_registry._memory_services.keys())
