"""System instructions and capabilities."""


class SystemInstructions:
    """Canonical system prompt with tool capabilities."""

    def format(self, tools: dict = None) -> str:
        """System instructions with tool capabilities."""
        base = """You are a helpful AI assistant.

RESPOND USING THIS XML STRUCTURE:
<thinking>your reasoning</thinking>
<tools>[{"name": "tool_name", "args": {"param": "value"}}] OR []</tools>
<response>your answer</response>

TOOL CALL FORMAT:
- Use JSON objects with "name" and "args" fields
- Example: [{"name": "file_write", "args": {"filename": "test.txt", "content": "hello"}}]
- For no tools: []
"""

        from ..lib.security import SEMANTIC_SECURITY

        if tools:
            tool_list = "\n".join(f"- {t.name}: {t.description}" for t in tools.values())
            tools_section = f"\nTOOLS:\n{tool_list}\n"
        else:
            tools_section = ""

        return base + SEMANTIC_SECURITY + tools_section


# Singleton instance
system = SystemInstructions()
