"""Conversation context namespace - message history.

Provides conversation continuity through persistent message history.
Conversation-scoped threading that survives across multiple tasks.
"""

from typing import Optional, Any


class ConversationContext:
    """Conversation domain context - persistent message history."""
    
    def __init__(self, state: Any):
        """Initialize conversation context.
        
        Args:
            state: Current agent state containing conversation
        """
        self.state = state
    
    async def build(self) -> Optional[str]:
        """Build conversation context from message history.
        
        Returns conversation summary for context, not full messages.
        Full messages are handled by reasoning system directly.
        
        Returns:
            Conversation summary string or None
        """
        if not self.state.conversation or not self.state.conversation.messages:
            return None
            
        messages = self.state.conversation.messages
        if not messages:
            return None
            
        # Build conversation summary for context awareness
        message_count = len(messages)
        last_message = messages[-1] if messages else None
        
        if message_count == 1:
            return f"CONVERSATION: New conversation (1 message)"
        elif last_message:
            role = last_message.get("role", "unknown")
            content_preview = (last_message.get("content", ""))[:100]
            return f"CONVERSATION: Ongoing conversation ({message_count} messages, last: {role})"
        
        return f"CONVERSATION: Ongoing conversation ({message_count} messages)"