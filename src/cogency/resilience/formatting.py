"""User-friendly error messages - clean templates."""

import re
from typing import Any, Dict, Optional

# Unified error message templates
TEMPLATES = {
    "TOOL_TIMEOUT": "The {tool_name} operation timed out.",
    "TOOL_NETWORK": "I encountered a network issue with {tool_name}. Please try again.",
    "TOOL_INVALID": "I couldn't run {tool_name} - missing required information.",
    "LLM_ERROR": "I'm having trouble connecting to the AI service. Please try again.",
    "REASONING_LOOP": "I noticed I was repeating the same approach. Let me try differently.",
    "MAX_ITERATIONS": "I've tried several approaches. Here's what I found so far.",
    "PARSING_FAILED": "I had trouble formatting my response. Let me try again.",
    "MEMORY_FAILED": "I couldn't access memory for this conversation, but I can still help.",
    "UNKNOWN": "I encountered an unexpected issue. Let me try to help anyway.",
}


def get_user_message(error_type: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Convert technical errors to user-friendly messages."""
    context = context or {}
    template = TEMPLATES.get(error_type, TEMPLATES["UNKNOWN"])

    try:
        return template.format(**context)
    except KeyError:
        return TEMPLATES["UNKNOWN"]


def format_tool_error(tool_name: str, error: Exception) -> str:
    """Format tool errors for users."""
    error_str = str(error).lower()

    if "timeout" in error_str:
        return get_user_message("TOOL_TIMEOUT", {"tool_name": tool_name})
    elif "network" in error_str or "connection" in error_str:
        return get_user_message("TOOL_NETWORK", {"tool_name": tool_name})
    else:
        return get_user_message("TOOL_INVALID", {"tool_name": tool_name})


def sanitize_error(error_msg: str) -> str:
    """Remove technical jargon from error messages."""
    # Remove traceback patterns
    patterns = [
        r"Traceback \\(most recent call last\\):.*",
        r'File ".*", line \\d+.*',
        r"(AttributeError|ValueError|KeyError|TypeError):.*",
    ]

    for pattern in patterns:
        error_msg = re.sub(pattern, "", error_msg, flags=re.DOTALL)

    error_msg = " ".join(error_msg.split())
    return error_msg[:200] + "..." if len(error_msg) > 200 else error_msg or "Unexpected issue"
