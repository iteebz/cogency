"""Storage interfaces for agent persistence.

This module provides clean storage interfaces:

State Storage (Agent Persistence):
- StateStore: Base interface for agent state persistence
- SQLite: Local file-based state storage with vector support
- Supabase: Cloud-based state storage

Example:
    ```python
    from cogency.storage.state import SQLite

    store = SQLite("agent_state.db")
    await store.save_profile(user_id, profile)
    ```

Vector operations are handled by cogency.semantic module.
"""

# Import state storage domain
from .state import SQLite, StateStore, Supabase

__all__ = [
    "StateStore",
    "SQLite", 
    "Supabase",
]
