"""System instructions and capabilities."""


def system(tools: dict = None, iteration: int = 0) -> str:
    """System instructions with security assessment and tool capabilities."""
    parts = [
        "You are a helpful AI assistant. Use the XML sectioned format for all responses:",
        "",
        "<thinking>",
        "Your reasoning process here",
        "</thinking>",
        "",
        "<tools>",
        '[{"name": "tool_name", "args": {"param": "value"}}]',
        "</tools>",
        "",
        "<response>",
        "Your final response here",
        "</response>",
    ]

    # Security assessment on first iteration only
    if iteration == 0:
        from ..lib.security import SECURITY_ASSESSMENT

        parts.insert(1, SECURITY_ASSESSMENT)
        parts.insert(2, "")

    # Tool descriptions
    if tools:
        tools_text = "AVAILABLE TOOLS:\n" + "\n".join(
            f"- {t.name}: {t.description}" for t in tools.values()
        )
        parts.insert(-6, tools_text)
        parts.insert(-6, "")

    return "\n".join(parts)
