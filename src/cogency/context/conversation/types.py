"""Conversation domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class Conversation:
    """Persistent conversation history across tasks."""

    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
