from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseTool(ABC):
    """Base class for all tools in the cogency framework."""

    def __init__(self, name: str, description: str):
        """Initialize the tool with a name and description.

        Args:
            name: The name of the tool (used for tool calls)
            description: Human-readable description of what the tool does
        """
        self.name = name
        self.description = description

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute tool with automatic error handling - USE THIS, NOT run() directly."""
        try:
            return await self.run(**kwargs)
        except Exception as e:
            # Use the same beautiful error formatting as @graceful decorator
            from cogency.errors import format_tool_error
            return format_tool_error(e, self.name, "run")

    @abstractmethod
    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the tool with the given parameters.

        Returns:
            Dict containing the tool's results or error information
        """
        pass

    @abstractmethod
    def get_schema(self) -> str:
        """Return tool call schema for LLM formatting.

        Returns:
            String representation of the tool's parameter schema
        """
        pass

    @abstractmethod
    def get_usage_examples(self) -> List[str]:
        """Return example tool calls for LLM guidance.

        Returns:
            List of example tool call strings
        """
        pass
