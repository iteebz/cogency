"""Persist services."""

from typing import Optional, Type

from cogency.utils.registry import Provider

from .base import Store, _setup_persist  # noqa: F401
from .filesystem import Filesystem

# Provider registry
_persist_provider = Provider(
    {
        "filesystem": Filesystem,
    },
    default="filesystem",
)


def _store(provider: Optional[str] = None) -> Type[Store]:
    """Get persist store - internal utility."""
    return _persist_provider.get(provider)


__all__ = ["Store", "Filesystem"]
