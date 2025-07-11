from typing import List, Dict, Any

class Context:
    """Agent operational context."""
    def __init__(self, current_input: str, messages: List[Dict[str, str]] = None):
        self.current_input = current_input
        self.messages = messages if messages is not None else []

    def add_message(self, role: str, content: str):
        """Adds message to history."""
        self.messages.append({"role": role, "content": content})

    def __repr__(self):
        return f"Context(current_input='{self.current_input}', messages={len(self.messages)} messages)"