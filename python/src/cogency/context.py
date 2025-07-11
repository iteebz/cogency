from typing import Any, Optional

class Context:
    """Agent operational context."""
    def __init__(self, current_input: str, messages: list[dict[str, str]] = None, tool_call_details: Optional[dict[str, Any]] = None):
        self.current_input = current_input
        self.messages = messages if messages is not None else []
        self.tool_call_details = tool_call_details

    def add_message(self, role: str, content: str, tool_call_id: Optional[str] = None):
        """Adds message to history."""
        message_dict = {"role": role, "content": content}
        if tool_call_id:
            message_dict["tool_call_id"] = tool_call_id
        self.messages.append(message_dict)

    def __repr__(self):
        return f"Context(current_input='{self.current_input}', messages={len(self.messages)} messages)"