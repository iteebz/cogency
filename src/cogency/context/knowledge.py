"""User knowledge and document management."""

from typing import Any, Optional

from ..lib.storage import add_document, search_documents


class UserKnowledge:
    """User-scoped knowledge base and document storage."""

    def format(self, query: str, user_id: str) -> str:
        """Format knowledge search results for context display."""
        try:
            results = self.search(query, user_id, limit=3)
            if not results:
                return ""

            lines = []
            for r in results:
                content = r["content"][:150]
                if len(r["content"]) > 150:
                    content += "..."
                lines.append(f"📄 {r['doc_id']}: {content}")

            return "Relevant knowledge:\n" + "\n\n".join(lines)
        except Exception:
            return ""

    def search(self, query: str, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search user's knowledge base."""
        try:
            # TODO: Implement user-scoped search when storage supports it
            return search_documents(query, limit=limit) or []
        except Exception:
            return []

    def store(
        self, user_id: str, doc_id: str, content: str, metadata: dict[str, Any] = None
    ) -> bool:
        """Store document in user's knowledge base."""
        try:
            # TODO: Make user-scoped when storage supports it
            return add_document(doc_id, content, metadata or {})
        except Exception:
            return False

    def get(self, user_id: str, doc_id: str) -> Optional[dict[str, Any]]:
        """Get specific document from user's knowledge base."""
        try:
            # TODO: Implement user-scoped retrieval when storage supports it
            return None
        except Exception:
            return None

    def list(self, user_id: str) -> list[dict[str, Any]]:
        """List all documents in user's knowledge base."""
        try:
            # TODO: Implement user-scoped listing when storage supports it
            return []
        except Exception:
            return []

    def delete(self, user_id: str, doc_id: str) -> bool:
        """Delete document from user's knowledge base."""
        try:
            # TODO: Implement user-scoped deletion when storage supports it
            return False
        except Exception:
            return False


# Singleton instance
knowledge = UserKnowledge()
