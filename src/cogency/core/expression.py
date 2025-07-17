"""Four orthogonal axes of agent expression - personality, system_prompt, tone, style."""

def compose_system_prompt(personality: str = None, system_prompt: str = None, tone: str = None, style: str = None) -> str:
    """Compose the four orthogonal axes into a coherent system prompt."""
    # If explicit system_prompt provided, use it directly
    if system_prompt:
        return system_prompt
    
    # Otherwise, compose from personality, tone, and style
    parts = []
    
    # Base identity
    if personality:
        parts.append(f"You are {personality}.")
    else:
        parts.append("You are a helpful AI assistant.")
    
    # Communication style
    style_parts = []
    if tone:
        style_parts.append(f"tone: {tone}")
    if style:
        style_parts.append(f"style: {style}")
    
    if style_parts:
        parts.append(f"Communicate with {', '.join(style_parts)}.")
    
    # Core behavior
    parts.append("Always be helpful, accurate, and thoughtful in your responses.")
    
    return " ".join(parts)