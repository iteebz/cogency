"""Standardized tool result patterns - beautiful, consistent, extensible."""
from typing import Any, Dict, Optional, Union


class ToolResult:
    """Standardized tool result - all tools return this pattern."""
    
    def __init__(self, success: bool, data: Any = None, error: str = None, metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {"success": self.success}
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def ok(cls, data: Any, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Create successful result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def failure(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Create failure result."""
        return cls(success=False, error=error, metadata=metadata)
    
    def __bool__(self) -> bool:
        """Allow if result: checks."""
        return self.success
    
    def __repr__(self) -> str:
        if self.success:
            return f"ToolResult.ok(data={repr(self.data)})"
        else:
            return f"ToolResult.failure(error={repr(self.error)})"


def get_data(tool_output: Any) -> Any:
    """Extract data from any tool output format - handles legacy and new patterns."""
    if isinstance(tool_output, ToolResult):
        return tool_output.data if tool_output.success else None
    elif isinstance(tool_output, dict):
        # Handle legacy patterns
        if "success" in tool_output:
            # Web search pattern: {success: true, data: ...}
            return tool_output if tool_output.get("success") else None
        elif "result" in tool_output:
            # Calculator/file manager pattern: {result: ...} or {error: ...}
            return tool_output.get("result")
        elif "error" in tool_output:
            # Error pattern
            return None
        else:
            # Direct data pattern (weather, timezone)
            return tool_output
    else:
        # Raw data
        return tool_output


def is_success(tool_output: Any) -> bool:
    """Check if tool output represents success - handles all patterns."""
    if isinstance(tool_output, ToolResult):
        return tool_output.success
    elif isinstance(tool_output, dict):
        if "success" in tool_output:
            return tool_output.get("success", False)
        elif "error" in tool_output:
            return False
        else:
            # Direct data or result pattern - assume success if not None
            return tool_output is not None
    else:
        # Raw data - assume success if not None
        return tool_output is not None


def get_error(tool_output: Any) -> Optional[str]:
    """Extract error message from tool output - handles all patterns."""
    if isinstance(tool_output, ToolResult):
        return tool_output.error if not tool_output.success else None
    elif isinstance(tool_output, dict):
        return tool_output.get("error")
    else:
        return None