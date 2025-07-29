"""Persist services - automagical discovery."""

from typing import Optional, Type

from cogency.utils import Provider

from .base import Store, setup_persistence
from .filesystem import Filesystem

# Provider registry
_persist_provider = Provider(
    {
        "filesystem": Filesystem,
    },
    default="filesystem",
)


def get_store(provider: Optional[str] = None) -> Type[Store]:
    """Get persist store with automagical discovery."""
    return _persist_provider.get(provider)


__all__ = ["Store", "get_store", "setup_persistence", "Filesystem"]
