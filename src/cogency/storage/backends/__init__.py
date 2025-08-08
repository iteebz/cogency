"""Storage backends - SQLite + Supabase for canonical Three-Horizon Model."""

from typing import Optional

from .base import Store
from .sqlite import SQLite

# Optional Supabase provider
_providers = {
    "sqlite": SQLite,
}

try:
    from .supabase import Supabase

    _providers["supabase"] = Supabase
except ImportError:
    pass  # Supabase not available


def get_store(provider: Optional[str] = None) -> Store:
    """Get storage backend - SQLite (local) or Supabase (production)."""
    if provider == "supabase" and "supabase" in _providers:
        return _providers["supabase"]()
    return _providers["sqlite"]()  # Default to SQLite


__all__ = ["Store", "SQLite", "get_store"]

# Add Supabase to exports if available
if "supabase" in _providers:
    __all__.append("Supabase")
