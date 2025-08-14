"""SQLite storage operations - functional composition over inheritance.

Canonical domain operations as standalone functions.
No god-objects, no multiple inheritance ceremony.
"""

from .sqlite.conversations import (
    create_conversation,
    delete_conversation,
    list_conversations,
    load_conversation,
    save_conversation,
)
from .sqlite.knowledge import (
    delete_knowledge_vector,
    save_knowledge_vector,
    search_knowledge_vectors,
)
from .sqlite.profiles import create_profile, delete_profile, load_profile, save_profile
from .sqlite.workspaces import (
    clear_workspace,
    list_workspaces,
    load_workspace_data,
    save_workspace_data,
)

__all__ = [
    # Profiles
    "create_profile",
    "load_profile",
    "save_profile",
    "delete_profile",
    # Conversations
    "create_conversation",
    "load_conversation",
    "save_conversation",
    "delete_conversation",
    "list_conversations",
    # Workspaces
    "save_workspace_data",
    "load_workspace_data",
    "clear_workspace",
    "list_workspaces",
    # Knowledge
    "save_knowledge_vector",
    "search_knowledge_vectors",
    "delete_knowledge_vector",
]
