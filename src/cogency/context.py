import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional


# Avoid circular import
if TYPE_CHECKING:
    pass

# Internal filtering constants
INTERNAL_ACTIONS = {"tool_needed", "direct_response"}
STATUS_VALUES = {"continue", "complete", "error"}
SYSTEM_PREFIXES = ("TOOL_CALL:",)


# Context: Conversation state (user input + message history)
# AgentState: LangGraph workflow state container (includes Context + execution trace)
class Context:
    """Agent operational context."""

    def __init__(
        self,
        current_input: str,
        messages: List[Dict[str, str]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        max_history: Optional[int] = 20,  # Default limit: 20 messages (rolling window)
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        user_id: str = "default",
    ):
        self.current_input = current_input
        self.messages = messages or []
        self.tool_results = tool_results or []
        self.max_history = max_history
        self.conversation_history = conversation_history or []
        self.user_id = user_id
        
        # Apply initial limit if messages were provided
        if self.messages:
            self._apply_history_limit()

    def add_message(self, role: str, content: str, trace_id: Optional[str] = None):
        """Add message to history with optional trace linkage."""
        message_dict = {"role": role, "content": content}
        if trace_id:
            message_dict["trace_id"] = trace_id
        self.messages.append(message_dict)
        self._apply_history_limit()

    def _apply_sliding_window(self, items: List[Any]) -> List[Any]:
        """Apply sliding window limit to any list. Returns modified list."""
        if self.max_history is None or len(items) <= self.max_history:
            return items
        return [] if self.max_history == 0 else items[-self.max_history:]
    
    def _apply_history_limit(self):
        """Apply sliding window to messages."""
        self.messages = self._apply_sliding_window(self.messages)
    
    def _apply_conversation_history_limit(self):
        """Apply sliding window to conversation history."""
        self.conversation_history = self._apply_sliding_window(self.conversation_history)

    def add_tool_result(self, tool_name: str, args: dict, output: dict):
        """Add tool execution result to history."""
        self.tool_results.append({"tool_name": tool_name, "args": args, "output": output})
    
    def add_conversation_turn(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a conversation turn to history."""
        turn = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(turn)
        self._apply_conversation_history_limit()
    
    def get_recent_conversation(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the last n conversation turns."""
        return self.conversation_history[-n:] if self.conversation_history else []
    
    def clear_conversation_history(self):
        """Clear all conversation history."""
        self.conversation_history = []

    def get_clean_conversation(self) -> List[Dict[str, str]]:
        """Returns conversation without execution trace data and internal JSON."""

        clean_messages = []
        for msg in self.messages:
            content = msg["content"]
            # Filter out internal JSON messages
            if self._is_internal_message(content):
                continue
            # Filter out system messages
            if msg["role"] == "system":
                continue
            clean_messages.append({"role": msg["role"], "content": content})
        return clean_messages

    def _is_internal_message(self, content: str) -> bool:
        """Check if message content is internal/system generated."""
        if not isinstance(content, str):
            return False
        
        # Check for tool call prefixes
        if content.startswith(SYSTEM_PREFIXES):
            return True
        
        # Check for internal JSON
        try:
            data = json.loads(content)
            return (
                data.get("action") in INTERNAL_ACTIONS or
                data.get("status") in STATUS_VALUES
            )
        except (json.JSONDecodeError, TypeError):
            return False
    
    def __repr__(self):
        return (
            f"Context(current_input='{self.current_input}', messages={len(self.messages)} messages)"
        )
