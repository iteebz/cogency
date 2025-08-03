"""State persistence for agent continuity.

This module provides zero-ceremony state persistence for agents:

- Store: Base class for custom persistence backends
- Filesystem: Built-in filesystem-based persistence store

Internal functions handle state management but are not exposed in the public API.
Persistence is typically configured via PersistConfig in Agent setup.
"""

from .store import Store
from .store.filesystem import Filesystem

# Internal functions not exported:
# from .state import StatePersistence
# from .store import _store, _setup_persist
# from .utils import _get_state

__all__ = [
    # Public persistence APIs (advanced usage)
    "Store",  # Base class for custom stores
    "Filesystem",  # Built-in filesystem store
    # Internal APIs not exported:
    # - _store, _setup_persist, _get_state (framework internals)
    # - StatePersistence (implementation detail)
]
