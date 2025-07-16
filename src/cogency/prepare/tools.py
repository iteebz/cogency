"""Tool preparation utilities."""
from typing import List, Set, Dict, Any

from cogency.tools.base import BaseTool


def create_registry_lite(tools: List[BaseTool]) -> str:
    """Create enhanced registry with schemas for better tool selection."""
    entries = []
    for tool in tools:
        entry = f"- {tool.name}: {tool.description}"
        
        # Add schema if available - critical for LLM understanding tool params
        try:
            schema = tool.get_schema()
            if schema:
                entry += f"\n  Schema: {schema}"
        except (AttributeError, NotImplementedError):
            pass
            
        entries.append(entry)
    
    return "\n\n".join(entries)


def filter_tools_by_exclusion(tools: List[BaseTool], excluded_names: List[str]) -> List[BaseTool]:
    """Conservative filtering: exclude only specified tools, keep all others."""
    if not excluded_names:
        return tools
    
    excluded_set: Set[str] = set(excluded_names)
    return [tool for tool in tools if tool.name not in excluded_set]


def prepare_tools_for_react(selected_tools: List[BaseTool]) -> List[BaseTool]:
    """Prepare full tool registry with examples and parameters for ReAct."""
    # Filter out memorize tools - only keep recall and action tools
    react_tools = []
    for tool in selected_tools:
        if tool.name != 'memorize':  # Remove memorize tool
            react_tools.append(tool)
    
    return react_tools