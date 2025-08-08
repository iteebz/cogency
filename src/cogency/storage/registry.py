"""Store registry for consistent persistence across the application."""

from typing import Optional

from .backends.base import Store

# Global store registry
_global_store: Optional[Store] = None


def set_global_store(store: Store) -> None:
    """Set the global store instance for consistent persistence."""
    global _global_store
    _global_store = store


def get_global_store() -> Optional[Store]:
    """Get the global store instance."""
    return _global_store


def clear_global_store() -> None:
    """Clear the global store (mainly for testing)."""
    global _global_store
    _global_store = None
