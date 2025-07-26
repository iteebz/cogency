import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# Internal filtering constants
INTERNAL_ACTIONS = {"tool_needed", "response"}
STATUS_VALUES = {"continue", "complete", "error"}
SYSTEM_PREFIXES = ("TOOL_CALL:",)


# Context: Conversation state (user input + message history)
# State: LangGraph flow state container (includes Context + execution trace)
class Context:
    """Agent conversation context."""

    def __init__(
        self,
        query: str,
        messages: Optional[List[Dict[str, str]]] = None,
        max_history: Optional[int] = 20,  # Default limit: 20 messages (rolling window)
        history: Optional[List[Dict[str, Any]]] = None,
        user_id: str = "default",
    ):
        self.query = query
        self.chat = messages or []  # Active LLM conversation
        self.max_history = max_history
        self.archive = history or []  # Completed conversation turns
        self.user_id = user_id
        self.tool_log: List[Dict[str, Any]] = []  # Tool execution audit trail

        # Apply initial limit if messages were provided
        if self.chat:
            self._limit_history()

    def add_message(self, role: str, content: str, trace_id: Optional[str] = None) -> None:
        """Add message to active chat."""
        message_dict = {"role": role, "content": content}
        if trace_id:
            message_dict["trace_id"] = trace_id
        self.chat.append(message_dict)
        self._limit_history()

    def _apply_limit(self, items: List[Any]) -> List[Any]:
        """Apply sliding window limit to list."""
        if self.max_history is None or len(items) <= self.max_history:
            return items
        return [] if self.max_history == 0 else items[-self.max_history :]

    def _limit_history(self) -> None:
        """Limit active chat history."""
        self.chat = self._apply_limit(self.chat)

    def _limit_turns(self) -> None:
        """Limit archived turns."""
        self.archive = self._apply_limit(self.archive)

    def add_result(self, tool_name: str, args: Dict[str, Any], output: Dict[str, Any]) -> None:
        """Add tool execution to audit log."""
        self.tool_log.append({"tool_name": tool_name, "args": args, "output": output})

    def add_turn(
        self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add conversation turn."""
        turn = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.archive.append(turn)
        self._limit_turns()

    def recent_turns(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get last n conversation turns, filtering out system and internal messages."""
        # Filter out system and internal messages
        clean_turns = []
        for turn in self.archive:
            # Skip system messages
            if turn["query"] == "system":
                continue
            # Skip internal messages
            if self._is_internal(turn["response"]):
                continue
            # Convert to expected format for test compatibility
            clean_turn = {
                "role": turn["query"],
                "content": turn["response"],
                "timestamp": turn["timestamp"],
            }
            clean_turns.append(clean_turn)

        return clean_turns[-n:] if clean_turns else []

    def clear_history(self) -> None:
        """Clear conversation archive."""
        self.archive = []

    def get_clean_conversation(self) -> List[Dict[str, str]]:
        """Get conversation without system messages."""

        clean_messages = []
        for msg in self.chat:
            content = msg["content"]
            # Filter out internal JSON messages
            if self._is_internal(content):
                continue
            # Filter out system messages
            if msg["role"] == "system":
                continue
            clean_messages.append({"role": msg["role"], "content": content})
        return clean_messages

    def _is_internal(self, content: str) -> bool:
        """Detect internal system messages."""
        if not isinstance(content, str):
            return False

        # Check for tool call prefixes
        if content.startswith(SYSTEM_PREFIXES):
            return True

        # Check for internal JSON
        try:
            data = json.loads(content)
            return data.get("action") in INTERNAL_ACTIONS or data.get("status") in STATUS_VALUES
        except (json.JSONDecodeError, TypeError):
            return False

    def __repr__(self) -> str:
        return f"Context(query='{self.query}', chat={len(self.chat)} messages)"
