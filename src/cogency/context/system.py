"""System prompt generation."""

SYSTEM_PROMPT = """You MUST use structured delimiters for tool execution:

§RESPOND: your message to the user (use multiple times as needed)
§THINK: optional reasoning scratch pad
§CALL: {"name": "tool_name", "args": {"key": "value"}}
§EXECUTE
§END: when task complete

CRITICAL: Every §CALL must be immediately followed by §EXECUTE

Examples:

Simple task:
§RESPOND: I'll check the files here
§CALL: {"name": "file_list", "args": {"path": "."}}
§EXECUTE
§RESPOND: Found 12 files - mostly Python scripts
§END

Multi-step with reasoning:
§RESPOND: I'll analyze this codebase for issues
§THINK: Need to understand structure first, then check for common problems
§CALL: {"name": "file_search", "args": {"pattern": "*.py"}}
§EXECUTE
§RESPOND: Found 5 Python files, checking the main entry point
§CALL: {"name": "file_read", "args": {"file": "main.py"}}
§EXECUTE  
§THINK: I see wildcard imports which could cause namespace issues
§RESPOND: Found import issue - fixing it now
§CALL: {"name": "file_edit", "args": {"file": "main.py", "old": "from utils import *", "new": "from utils import helper_function"}}
§EXECUTE
§RESPOND: Fixed wildcard import - codebase should run cleanly now
§END"""

SECURITY_SECTION = """\n\nWork within project scope and avoid system areas. Use structured tools when possible."""


def prompt(tools: list = None, instructions: str = None, include_security: bool = True) -> str:
    """Generate minimal viable prompt for maximum emergence.
    
    Core principles:
    - RESPOND: Multiple times, LLM choice timing
    - THINK: Optional reasoning scratch pad
    - CALL + EXECUTE: Always paired, no exceptions
    - END: LLM decides when complete
    - Security: Semantic high-level principles
    - Universal: Same prompt all providers/modes
    """

    # Core protocol (protected from user modification)
    base = SYSTEM_PROMPT + (SECURITY_SECTION if include_security else "")

    # User steering layer
    if instructions:
        base += f"\n\nINSTRUCTIONS: {instructions}"

    # Dynamic context layer
    if tools:
        from ..tools import instructions

        tool_registry = instructions(tools)
        base += f"\n\n{tool_registry}"
    else:
        base += "\n\nNo tools available."

    return base
