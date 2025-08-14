"""Task session coordination - lightweight metadata container.

Minimal coordination object that holds IDs and metadata without domain logic.
All actual functionality lives in domain operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class TaskSession:
    """Lightweight task coordination - metadata only, no logic.

    Contains only coordination metadata. All domain operations
    (conversation, working state, execution) are handled by their
    respective domain primitives.
    """

    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(uuid4()))

    # Coordination metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Optional conversation linking
    conversation_id: str | None = None


__all__ = ["TaskSession"]
