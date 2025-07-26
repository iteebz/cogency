"""Agent services and tools setup utilities."""

from typing import Any, List, Optional

from cogency.services.memory.filesystem import FileBackend
from cogency.tools.registry import ToolRegistry


def agent_services(opts: dict[str, Any]) -> tuple[List[Any], Optional[Any]]:
    """Setup tools and memory services for agent with clean API."""

    # Handle memory service
    memory_enabled = opts.get("memory", True)
    if memory_enabled:
        memory = opts.get("memory_backend") or FileBackend(
            opts.get("memory_dir", ".cogency/memory")
        )
    else:
        memory = None

    # Handle tools - only accept instances, not classes
    tools = opts.get("tools")
    if tools is not None:
        # Validate that all tools are instances, not classes
        for tool in tools:
            if isinstance(tool, type):
                raise ValueError(
                    f"Tool {tool.__name__} must be instantiated. "
                    f"Use {tool.__name__}() instead of {tool.__name__}"
                )
    else:
        # Auto-discover all registered tools
        if memory:
            tools = ToolRegistry.get_tools(memory=memory)
        else:
            tools = ToolRegistry.get_tools()

    # Add Recall tool if memory is enabled and not already in tools
    if memory_enabled and memory:
        from cogency.tools.recall import Recall

        # Check if Recall is already in tools
        has_recall = any(isinstance(tool, Recall) for tool in tools)
        if not has_recall:
            tools.append(Recall(memory))

    return tools, memory
