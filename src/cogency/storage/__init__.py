"""Storage interfaces for agent persistence and retrieval.

This module provides clean storage interfaces for different domains:

State Storage (Agent Persistence):
- StateStore: Base interface for agent state persistence
- SQLite: Local file-based state storage
- Supabase: Cloud-based state storage

Vector Storage (Document Retrieval):
- VectorStore: Base interface for semantic search
- FileStore: Local embeddings from JSON files

Example:
    State storage:

    ```python
    from cogency.storage.state import SQLite

    store = SQLite("agent_state.db")
    await store.save_user_profile(user_id, profile)
    ```

    Vector storage:

    ```python
    from cogency.storage.vector import FileStore

    store = FileStore("embeddings.json")
    results = await store.search(query_embedding, top_k=5)
    ```
"""

# Import state storage domain
from .state import SQLite, StateStore, Supabase

# Import vector storage domain
from .vector import FileStore, VectorStore

__all__ = [
    # State storage
    "StateStore",
    "SQLite",
    "Supabase",
    # Vector storage
    "VectorStore",
    "FileStore",
]
