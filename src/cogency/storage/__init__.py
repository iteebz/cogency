"""State persistence for agent continuity.

This module provides zero-ceremony state persistence for agents:

- Store: Base class for custom persistence backends
- SQLite/Supabase: CANONICAL Three-Horizon backends

Internal functions handle state management but are not exposed in the public API.
Persistence is typically configured via PersistConfig in Agent setup.
"""

from .backends import Store
from .backends.sqlite import SQLite
from .backends.supabase import Supabase

# Internal functions not exported:
# from .state import Persistence
# from .store import _store, _setup_persist
# from .utils import _get_state

__all__ = [
    # Public persistence APIs (advanced usage)
    "Store",  # Base class for custom stores
    "SQLite",  # CANONICAL SQLite backend
    "Supabase",  # CANONICAL Supabase backend
    # Internal APIs not exported:
    # - _store, _setup_persist, _get_state (framework internals)
    # - Persistence (implementation detail)
]
