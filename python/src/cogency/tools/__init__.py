# Centralized Tool Registry
# Add new tools here to make them discoverable

from .calculator import CalculatorTool

# Default tool registry - import and add new tools here
AVAILABLE_TOOLS = [
    CalculatorTool,
]

# Tool registry by name for dynamic lookup
TOOL_REGISTRY = {
    tool.name: tool for tool in AVAILABLE_TOOLS
}

def get_tool_by_name(name: str):
    """Get tool class by name."""
    return TOOL_REGISTRY.get(name)

def list_available_tools():
    """List all available tool names."""
    return list(TOOL_REGISTRY.keys())