"""Emoji definitions for cogency output."""

# Emoji mapping - system/workflow emojis only (tools define their own)
emoji = {
    # Core workflow phases
    "preprocess": "🔮",
    "reason": "🧠",
    "act": "⚡",
    "respond": "💬",
    "memory": "🧠",
    # State changes
    "trace": "🔧",
    "error": "❌",
    "success": "✅",
    "thinking": "💭",
    # System
    "agent": "🤖",
    "human": "👤",
    "tip": "💡",
    "info": "💡",
    "dependency": "🔒",
}

# Clear cognitive state indicators
cognitive_states = {
    # Reasoning states
    "thinking": {"emoji": "💭", "label": "Thinking..."},
    "reflecting": {"emoji": "🪞", "label": "Reflecting..."},
    "planning": {"emoji": "📝", "label": "Planning..."},
    "deciding": {"emoji": "🎯", "label": "Deciding..."},
    
    # Processing states  
    "preprocessing": {"emoji": "🔮", "label": "Preparing..."},
    "tool_selection": {"emoji": "🛠️", "label": "Selecting tools..."},
    "executing": {"emoji": "⚡", "label": "Executing..."},
    "responding": {"emoji": "💬", "label": "Responding..."},
    
    # Mode states
    "switching": {"emoji": "🔄", "label": "Switching mode..."},
    "escalating": {"emoji": "📈", "label": "Escalating to deep mode..."},
}


def tool_emoji(tool_name: str) -> str:
    """Get tool emoji with fallback to lightning bolt"""
    return emoji.get(tool_name.lower(), "⚡")


def format_cognitive_state(state_key: str, content: str = "") -> str:
    """Format cognitive state with clean emoji and label"""
    state = cognitive_states.get(state_key)
    if not state:
        return content
    
    emoji_label = f"{state['emoji']} {state['label']}\n"
    if content:
        return f"{emoji_label}{content}"
    return emoji_label
