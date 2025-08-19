"""User knowledge and document management."""

from typing import Any, Optional


class UserKnowledge:
    """User-scoped knowledge base and document storage."""

    def format(self, user_id: str) -> str:
        """Format user knowledge for context display."""
        # Knowledge disabled until proper user-scoped implementation
        return ""

    def search(self, query: str, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search user's knowledge base."""
        # Knowledge disabled until proper user-scoped implementation
        return []

    def store(
        self, user_id: str, doc_id: str, content: str, metadata: dict[str, Any] = None
    ) -> bool:
        """Store document in user's knowledge base."""
        # Knowledge disabled until proper user-scoped implementation
        return False

    def get(self, user_id: str, doc_id: str) -> Optional[dict[str, Any]]:
        """Get specific document from user's knowledge base."""
        # Knowledge disabled until proper user-scoped implementation
        return None

    def list(self, user_id: str) -> list[dict[str, Any]]:
        """List all documents in user's knowledge base."""
        # Knowledge disabled until proper user-scoped implementation
        return []

    def delete(self, user_id: str, doc_id: str) -> bool:
        """Delete document from user's knowledge base."""
        # Knowledge disabled until proper user-scoped implementation
        return False


# Singleton instance
knowledge = UserKnowledge()
