from typing import Any, Optional, TYPE_CHECKING

# Avoid circular import
if TYPE_CHECKING:
    from cogency.types import ExecutionTrace

class Context:
    """Agent operational context."""
    def __init__(self, current_input: str, messages: list[dict[str, str]] = None, tool_call_details: Optional[dict[str, Any]] = None, execution_trace: Optional["ExecutionTrace"] = None):
        self.current_input = current_input
        self.messages = messages if messages is not None else []
        self.tool_call_details = tool_call_details
        self.execution_trace = execution_trace

    def add_message(self, role: str, content: str):
        """Adds message to history."""
        message_dict = {"role": role, "content": content}
        self.messages.append(message_dict)

    def add_message_with_trace(self, role: str, content: str, trace_id: Optional[str] = None):
        """Adds message with optional trace linkage."""
        message_dict = {"role": role, "content": content}
        if trace_id and self.execution_trace:
            message_dict["trace_id"] = trace_id
        self.messages.append(message_dict)

    def get_clean_conversation(self) -> list[dict[str, str]]:
        """Returns conversation without execution trace data."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]

    def __repr__(self):
        trace_info = f", trace={self.execution_trace.trace_id}" if self.execution_trace else ""
        return f"Context(current_input='{self.current_input}', messages={len(self.messages)} messages{trace_info})"