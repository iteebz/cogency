"""Memory development tools for clean DX."""
from typing import Any, Dict, List

from .base import BaseTool
from .registry import tool
from ..memory.base import BaseMemory


@tool
class MemoryClearTool(BaseTool):
    """Clear all memory - dev tool."""

    def __init__(self, memory: BaseMemory):
        super().__init__(
            name="memory_clear",
            description="Clear all memory artifacts (development tool)"
        )
        self.memory = memory

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Clear all memory."""
        try:
            await self.memory.clear()
            return {"success": True, "message": "Memory cleared"}
        except Exception as e:
            return {"error": f"Failed to clear memory: {str(e)}"}

    def get_schema(self) -> str:
        return "memory_clear()"

    def get_usage_examples(self) -> List[str]:
        return ["memory_clear()"]


@tool
class MemoryInspectTool(BaseTool):
    """Inspect memory contents - dev tool."""

    def __init__(self, memory: BaseMemory):
        super().__init__(
            name="memory_inspect",
            description="Inspect memory contents and stats (development tool)"
        )
        self.memory = memory

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Inspect memory contents."""
        try:
            stats = await self.memory.inspect()
            return {"success": True, "stats": stats}
        except Exception as e:
            return {"error": f"Failed to inspect memory: {str(e)}"}

    def get_schema(self) -> str:
        return "memory_inspect()"

    def get_usage_examples(self) -> List[str]:
        return ["memory_inspect()"]