"""SQLite Store implementation via domain composition."""

from .conversations import ConversationOperations
from .knowledge import KnowledgeOperations
from .profiles import ProfileOperations
from .workspaces import WorkspaceOperations


class SQLite(ProfileOperations, ConversationOperations, WorkspaceOperations, KnowledgeOperations):
    """SQLite Store implementation via canonical domain composition.

    Implements the Store protocol by composing domain-specific operations:
    - ProfileOperations: User identity persistence
    - ConversationOperations: Message history persistence
    - WorkspaceOperations: Task-scoped state persistence
    - KnowledgeOperations: Semantic memory persistence

    Each domain module is ~50-80 lines, maintaining Beauty Doctrine compliance.
    """

    pass


__all__ = ["SQLite"]
