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

    def validate_and_run(self, **kwargs: Any) -> Dict[str, Any]:
        """Validate parameters then run the tool."""
        try:
            return self.run(**kwargs)
        except Exception as e:
            return {"error": str(e)}

    @abstractmethod
    def run(self, **kwargs: Any) -> Dict[str, Any]:
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
