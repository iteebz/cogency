"""System instructions."""


def system(tools: list = None) -> str:
    """Base system instructions with optional tool definitions."""
    base = "You are a helpful AI assistant. Provide clear, concise responses."
    
    if tools:
        tool_descriptions = "\n".join(f"- {t.name}: {t.description}" for t in tools)
        return f"{base}\n\nAvailable tools:\n{tool_descriptions}\n\nTo use a tool, respond with JSON: {{\"tool\": \"tool_name\", \"args\": {{\"param\": \"value\"}}}}\nTo respond normally, just write your response."
    
    return base
