"""Conversation subdomain - conversational intelligence and continuity.

CONVERSATION DOMAIN SCOPE:
The conversation domain encompasses all aspects of conversational context and intelligence,
providing rich communication awareness beyond simple message history.

CURRENT IMPLEMENTATION (Minimal):
- Basic message history formatting for immediate context
- Single conversation persistence and retrieval

FULL DOMAIN VISION (Future):
1. **Current Session Context**:
   - Active message history with intelligent windowing
   - Message threading and context preservation
   - Turn-taking patterns and conversational flow analysis
   - Real-time conversation state tracking

2. **Historical Conversation Intelligence**:
   - Semantic search across all past conversations
   - Cross-conversation topic threading ("we discussed X before")
   - Pattern matching similar conversational contexts
   - Conversation clustering by topic, intent, or outcome

3. **Conversation Summarization & Compression**:
   - Intelligent conversation summarization for long threads
   - Topic extraction and conversational arc analysis
   - Multi-level summarization (message → turn → conversation → topic)
   - Conversation continuity preservation across sessions

4. **Message-Level Intelligence**:
   - Individual message analysis, intent detection, and categorization
   - Communication style and preference learning
   - Context-aware message interpretation and formatting
   - Conversational repair and clarification handling

5. **Conversational Memory & Learning**:
   - Long-term conversational pattern recognition
   - User communication preference adaptation
   - Conversational success pattern identification
   - Cross-session conversational state persistence

ARCHITECTURAL PRINCIPLE:
Conversation context is not just "message history" - it's conversational intelligence.
The domain provides rich understanding of communication patterns, preferences, and continuity
to enable natural, context-aware conversational AI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


@dataclass
class Conversation:
    """Persistent conversation history across tasks."""

    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class ConversationContext:
    """Conversation domain context - message history injection."""
    
    def __init__(self, conversation: Conversation):
        self.conversation = conversation
    
    async def build(self) -> Optional[str]:
        """Build conversation context from message history."""
        if not self.conversation or not self.conversation.messages:
            return None
            
        # Format recent messages for context
        messages = self.conversation.messages[-10:]  # Last 10 messages
        if not messages:
            return None
            
        context_parts = ["CONVERSATION HISTORY:"]
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content:
                # Truncate long messages
                truncated = content[:200] + "..." if len(content) > 200 else content
                context_parts.append(f"{role.upper()}: {truncated}")
        
        return "\n".join(context_parts)


# Import operations for single-import convenience
from .operations import (
    create_conversation,
    load_conversation,
    save_conversation,
    add_message,
    get_messages_for_llm,
    get_recent_messages,
)

__all__ = [
    "Conversation", 
    "ConversationContext",
    # Operations
    "create_conversation",
    "load_conversation", 
    "save_conversation",
    "add_message",
    "get_messages_for_llm",
    "get_recent_messages",
]