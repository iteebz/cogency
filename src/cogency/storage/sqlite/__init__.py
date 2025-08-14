"""SQLite storage operations - functional composition.

ELIMINATED ARCHITECTURAL VIOLATION: Multiple inheritance god-object.
Domain operations are now standalone functions in their respective modules.
Use direct imports: from cogency.storage.sqlite.profiles import save_profile
"""

# Re-export functional operations for convenience
from .conversations import (
    create_conversation,
    delete_conversation,
    list_conversations,
    load_conversation,
    load_conversation_data,
    save_conversation,
    save_conversation_data,
)
from .knowledge import delete_knowledge_vector, save_knowledge_vector, search_knowledge_vectors
from .profiles import create_profile, delete_profile, load_profile, save_profile
from .workspaces import clear_workspace, list_workspaces, load_workspace_data, save_workspace_data

__all__ = [
    # Profiles
    "create_profile",
    "load_profile",
    "save_profile",
    "delete_profile",
    # Conversations
    "create_conversation",
    "load_conversation",
    "load_conversation_data",
    "save_conversation",
    "save_conversation_data",
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
