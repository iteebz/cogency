"""Tool execution outcome types."""

from enum import Enum


class ToolOutcome(Enum):
    """Standardized tool execution results."""
    
    SUCCESS = "success"    # Tool executed successfully with expected output
    FAILURE = "failure"    # Tool executed but failed (e.g., file not found)
    ERROR = "error"        # Tool execution error (e.g., syntax error, crash)
    TIMEOUT = "timeout"    # Tool execution exceeded time limit