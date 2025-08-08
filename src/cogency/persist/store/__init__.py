"""Persist services."""

from typing import Optional

from cogency.utils.registry import Provider

from .base import Store, _setup_persist  # noqa: F401
from .filesystem import Filesystem
from .sqlite import SQLiteStore

# Optional providers
_providers = {
    "filesystem": Filesystem,
    "sqlite": SQLiteStore,
}

# Add Supabase if available
try:
    from .supabase import SupabaseStore

    _providers["supabase"] = SupabaseStore
except ImportError:
    pass  # Supabase not installed

# Provider registry
_persist_provider = Provider(_providers, default="sqlite")


def get_store(provider: Optional[str] = None) -> Store:
    """Get persist store instance."""
    store_class = _persist_provider.get(provider)
    return store_class()


__all__ = ["Store", "Filesystem", "SQLiteStore"]

# Add Supabase to exports if available
if "supabase" in _providers:
    __all__.append("SupabaseStore")
