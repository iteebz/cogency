"""Tool registry for auto-discovery."""
from typing import List, Type
from .base import BaseTool


class ToolRegistry:
    """Auto-discovery registry for tools."""
    
    _tools: List[Type[BaseTool]] = []
    
    @classmethod
    def register(cls, tool_class: Type[BaseTool]):
        """Register a tool class for auto-discovery."""
        if tool_class not in cls._tools:
            cls._tools.append(tool_class)
        return tool_class
    
    @classmethod
    def get_tools(cls, **kwargs) -> List[BaseTool]:
        """Get all registered tool instances."""
        tools = []
        for tool_class in cls._tools:
            try:
                # First try without kwargs (most tools don't need them)
                tools.append(tool_class())
            except TypeError:
                try:
                    # Then try with kwargs (memory tools need them)
                    tools.append(tool_class(**kwargs))
                except TypeError:
                    # Skip tools that can't be instantiated
                    continue
        return tools
    
    @classmethod
    def clear(cls):
        """Clear registry (mainly for testing)."""
        cls._tools.clear()


def tool(cls):
    """Decorator to auto-register tools."""
    return ToolRegistry.register(cls)