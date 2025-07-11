from typing import Any, Optional, TYPE_CHECKING

# Avoid circular import
if TYPE_CHECKING:
    from cogency.types import ExecutionTrace

# Context: Conversation state (user input + message history)
# AgentState: LangGraph workflow state container (includes Context + execution trace)
class Context:
    """Agent operational context."""
    def __init__(self, current_input: str, messages: list[dict[str, str]] = None, tool_results: Optional[list[dict[str, Any]]] = None):
        self.current_input = current_input
        self.messages = messages if messages is not None else []
        self.tool_results = tool_results if tool_results is not None else []

    def add_message(self, role: str, content: str):
        """Adds message to history."""
        message_dict = {"role": role, "content": content}
        self.messages.append(message_dict)

    def add_message_with_trace(self, role: str, content: str, trace_id: Optional[str] = None):
        """Adds message with optional trace linkage."""
        message_dict = {"role": role, "content": content}
        if trace_id:
            message_dict["trace_id"] = trace_id
        self.messages.append(message_dict)
    
    def add_tool_result(self, tool_name: str, args: dict, output: dict):
        """Add tool execution result to history."""
        self.tool_results.append({
            "tool_name": tool_name,
            "args": args,
            "output": output
        })

    def get_clean_conversation(self) -> list[dict[str, str]]:
        """Returns conversation without execution trace data."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]

    def __repr__(self):
        return f"Context(current_input='{self.current_input}', messages={len(self.messages)} messages)"