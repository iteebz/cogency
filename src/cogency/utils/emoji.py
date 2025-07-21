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


def tool_emoji(tool_name: str) -> str:
    """Get tool emoji with fallback to lightning bolt"""
    return emoji.get(tool_name.lower(), "⚡")
