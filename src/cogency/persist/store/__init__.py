"""Persist services - automagical discovery."""

from typing import Optional, Type

from cogency.utils.discovery import AutoRegistry

from .base import Store, setup_persistence

# Automagical persist store discovery
_persist_registry = AutoRegistry("cogency.persist.store", Store)


def get_store(provider: Optional[str] = None) -> Type[Store]:
    """Get persist store with automagical discovery."""
    if provider is None:
        provider = "filesystem"  # Default
    return _persist_registry.get(provider)


# Make store classes available for direct import
_exported_classes = _persist_registry.all()
globals().update(_exported_classes)

__all__ = ["Store", "get_store", "setup_persistence"] + list(_exported_classes.keys())
