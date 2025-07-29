"""Memory services - automagical discovery."""

from typing import Optional, Type

from cogency.utils.discovery import AutoRegistry

from .base import Store, setup_memory

# Automagical memory store discovery
_memory_registry = AutoRegistry("cogency.memory.store", Store)


def get_store(provider: Optional[str] = None) -> Type[Store]:
    """Get memory store with automagical discovery."""
    if provider is None:
        provider = "filesystem"  # Default
    return _memory_registry.get(provider)


# Make store classes available for direct import
_exported_classes = _memory_registry.all()
globals().update(_exported_classes)

__all__ = ["Store", "get_store", "setup_memory"] + list(_exported_classes.keys())
