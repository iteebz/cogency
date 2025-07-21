from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseTool(ABC):
    """Base class for all tools in the cogency framework."""

    def __init__(self, name: str, description: str, emoji: str = "🛠️"):
        """Initialize the tool with a name, description, and visual emoji.

        Args:
            name: The name of the tool (used for tool calls)
            description: Human-readable description of what the tool does
            emoji: Visual emoji for this tool type (defaults to generic 🛠️)
        """
        self.name = name
        self.description = description
        self.emoji = emoji

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute tool with automatic error handling - USE THIS, NOT run() directly."""
        try:
            return await self.run(**kwargs)
        except Exception as e:
            # Use the same beautiful error formatting as @graceful decorator
            from cogency.errors import format_error
            return format_error(e, self.name, "run")

    @abstractmethod
    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the tool with the given parameters.

        Returns:
            Dict containing the tool's results or error information
        """
        pass

    @abstractmethod
    def schema(self) -> str:
        """Return tool call schema for LLM formatting.

        Returns:
            String representation of the tool's parameter schema
        """
        pass

    @abstractmethod
    def examples(self) -> List[str]:
        """Return example tool calls for LLM guidance.

        Returns:
            List of example tool call strings
        """
        pass
