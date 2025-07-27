from typing import Dict, List, Optional


class Context:
    """Minimal conversation context."""

    def __init__(
        self,
        query: str = "",
        messages: Optional[List[Dict[str, str]]] = None,
        user_id: str = "default",
    ):
        self.query = query
        self.messages = messages or []
        self.user_id = user_id

    def add_message(self, role: str, content: str) -> None:
        """Add message to chat."""
        self.messages.append({"role": role, "content": content})

    def get_conversation(self) -> List[Dict[str, str]]:
        """Get clean conversation for LLM."""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]

    def __repr__(self) -> str:
        return f"Context(query='{self.query}', messages={len(self.messages)} messages)"
