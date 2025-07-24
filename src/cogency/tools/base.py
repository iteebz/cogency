from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from cogency.utils.results import ToolResult


class BaseTool(ABC):
    """Base class for all tools in the cogency framework.

    Standardized tool interface requiring:
    - name, description, emoji: Tool identification
    - schema, examples, rules: LLM guidance (strings/lists in init)
    - run(): Core execution logic
    - format(): Display formatting for params and results
    """

    def __init__(
        self,
        name: str,
        description: str,
        emoji: str = "🛠️",
        schema: str = "",
        examples: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
    ):
        """Initialize the tool with metadata and LLM guidance.

        Args:
            name: The name of the tool (used for tool calls)
            description: Human-readable description of what the tool does
            emoji: Visual emoji for this tool type (defaults to generic 🛠️)
            schema: Tool call schema for LLM formatting
            examples: List of example tool calls for LLM guidance
            rules: List of usage rules and completion guidance
        """
        self.name = name
        self.description = description
        self.emoji = emoji
        self.schema = schema
        self.examples = examples or []
        self.rules = rules or []

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute tool with automatic error handling - USE THIS, NOT run() directly."""
        try:
            return await self.run(**kwargs)
        except Exception as e:
            from cogency.utils.results import ToolResult

            return ToolResult.fail(f"Tool execution failed: {str(e)}")

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given parameters.

        Returns:
            Dict containing the tool's results or error information
        """
        pass

    @abstractmethod
    def format_human(self, params: Dict[str, Any], results: Optional[Dict[str, Any]] = None) -> tuple[str, str]:
        """Format tool execution for human display."""
        pass

    @abstractmethod
    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format tool results for agent action history - show knowledge gained."""
        pass
