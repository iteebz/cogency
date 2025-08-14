"""Conversation operations - single source of truth.

All conversation lifecycle management, message handling, and persistence 
operations centralized in the conversation domain.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from . import Conversation

if TYPE_CHECKING:
    from cogency.storage.sqlite import SQLite


async def create_conversation(user_id: str, store: "SQLite") -> Conversation:
    """Create new conversation with persistence."""
    conversation = Conversation(user_id=user_id)
    await store.save_conversation(conversation)
    return conversation


async def load_conversation(conversation_id: str, user_id: str, store: "SQLite") -> Conversation | None:
    """Load existing conversation."""
    return await store.load_conversation(conversation_id, user_id)


async def save_conversation(conversation: Conversation, store: "SQLite") -> bool:
    """Save conversation changes."""
    conversation.last_updated = datetime.now()
    return await store.save_conversation(conversation)


def add_message(conversation: Conversation, role: str, content: str) -> None:
    """Add message to conversation.
    
    Args:
        conversation: Target conversation
        role: Message role (user, assistant, system)
        content: Message content
    """
    message = {
        "role": role,
        "content": content,
    }
    
    conversation.messages.append(message)
    conversation.last_updated = datetime.now()


def get_messages_for_llm(conversation: Conversation) -> list[dict]:
    """Get conversation messages for LLM interface.
    
    Returns copy to prevent mutations of conversation state.
    """
    if not conversation or not conversation.messages:
        return []
    return conversation.messages.copy()


def get_recent_messages(conversation: Conversation, count: int = 10) -> list[dict]:
    """Get recent messages for context."""
    if not conversation or not conversation.messages:
        return []
    return conversation.messages[-count:]


__all__ = [
    "create_conversation",
    "load_conversation", 
    "save_conversation",
    "add_message",
    "get_messages_for_llm",
    "get_recent_messages",
]