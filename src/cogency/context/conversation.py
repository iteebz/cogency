"""Conversation history management."""

from typing import Any

from ..lib.storage import load_conversations, save_conversations


class ConversationHistory:
    """User-scoped conversation and chat history management."""

    def format(self, conversation_id: str) -> str:
        """Format recent conversation history for context display."""
        try:
            messages = self.get(conversation_id)
            if not messages:
                return ""

            recent = messages[-5:] if len(messages) > 5 else messages
            lines = []
            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
                lines.append(f"{role}: {content}")

            return "Recent conversation:\n" + "\n".join(lines)
        except Exception:
            return ""

    def messages(self, conversation_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get conversation history as structured messages for LLM context."""
        messages = self.get(conversation_id, limit=limit)
        # Filter out corrupted messages with null content
        valid_messages = []
        for msg in messages:
            if isinstance(msg.get("content"), str) and msg.get("role"):
                valid_messages.append(msg)
        return valid_messages

    def get(self, conversation_id: str, limit: int = None) -> list[dict[str, Any]]:
        """Get conversation messages by conversation_id."""
        try:
            # Extract user_id from conversation_id pattern: user_id_timestamp
            if "_" in conversation_id:
                user_id = conversation_id.rsplit("_", 1)[0]
                all_messages = load_conversations(user_id) or []

                # Filter to only messages from this specific conversation
                messages = [
                    msg for msg in all_messages if msg.get("conversation_id") == conversation_id
                ]

                if limit is not None:
                    return messages[-limit:] if len(messages) > limit else messages
                return messages
            return []
        except Exception:
            return []

    def add(self, conversation_id: str, role: str, content: str) -> bool:
        """Add message to conversation history."""
        try:
            # Extract user_id for storage layer compatibility
            user_id = (
                conversation_id.rsplit("_", 1)[0] if "_" in conversation_id else conversation_id
            )

            # Load all user messages and append new one with conversation_id
            all_messages = load_conversations(user_id) or []
            all_messages.append(
                {"role": role, "content": content, "conversation_id": conversation_id}
            )

            save_conversations(user_id, all_messages)
            return True
        except Exception:
            return False

    def update(self, conversation_id: str, messages: list[dict[str, Any]]) -> bool:
        """Replace entire conversation history."""
        try:
            user_id = (
                conversation_id.rsplit("_", 1)[0] if "_" in conversation_id else conversation_id
            )
            save_conversations(user_id, messages)
            return True
        except Exception:
            return False

    def clear(self, conversation_id: str) -> bool:
        """Clear conversation history."""
        return self.update(conversation_id, [])

    def search(self, user_id: str, query: str, exclude_recent: int = 20) -> str:
        """Search user's conversation history, excluding recent messages to avoid overlap."""
        try:
            messages = load_conversations(user_id)
            if not messages:
                return "No history"

            # Exclude recent messages to avoid overlap with current context
            if len(messages) <= exclude_recent:
                return "No historical messages (all in current context)"

            historical_messages = messages[:-exclude_recent]

            query_words = [w.lower() for w in query.split() if len(w) > 2]
            if not query_words:
                return "Query too short"

            # Score historical messages by word overlap
            scored = []
            for msg in historical_messages[-200:]:  # Last 200 historical messages
                content = msg.get("content", "").lower()
                score = sum(1 for word in query_words if word in content)
                if score > 0:
                    scored.append((score, msg))

            if not scored:
                return f"No historical messages about '{query}'"

            # Return top 3 matches
            best = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
            results = [f"[{msg['role']}]: {msg['content'][:150]}..." for _, msg in best]

            return f"Found {len(scored)} historical matches:\n\n" + "\n\n".join(results)

        except Exception as e:
            return f"Search failed: {str(e)}"


# Singleton instance
conversation = ConversationHistory()
