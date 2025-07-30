"""Base tool interface - standardized execution, validation, and formatting."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from resilient_result import Result

from cogency.types import validate


class Tool(ABC):
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
        schema: str,
        emoji: str = "🛠️",
        params: Optional[Type] = None,
        examples: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
    ):
        """Initialize the tool with metadata and LLM guidance.

        Args:
            name: The name of the tool (used for tool calls)
            description: Human-readable description of what the tool does
            schema: Explicit schema string for LLM (e.g. "calculator(expression='2+2')")
            emoji: Visual emoji for this tool type (defaults to generic 🛠️)
            params: Optional dataclass for parameter validation
            examples: List of example tool calls for LLM guidance
            rules: List of usage rules and completion guidance
        """
        self.name = name
        self.description = description
        self.schema = schema
        self.emoji = emoji
        self.params = params
        self.examples = examples or []
        self.rules = rules or []

    # Schema is now explicit - no ceremony, just clean strings

    async def execute(self, **kwargs: Any) -> Result:
        """Execute tool with automatic validation and error handling - USE THIS, NOT run() directly."""
        try:
            # Validate params using dataclass schema if provided
            if self.params:
                validated_params = validate(kwargs, self.params)
                return await self.run(**validated_params.__dict__)

            # Fallback to direct execution if no schema
            return await self.run(**kwargs)
        except ValueError as e:
            # Schema validation errors
            return Result.fail(f"Invalid parameters: {str(e)}")
        except Exception as e:
            return Result.fail(f"Tool execution failed: {str(e)}")

    @abstractmethod
    async def run(self, **kwargs: Any) -> Result:
        """Execute the tool with the given parameters.

        Returns:
            Dict containing the tool's results or error information
        """
        pass

    # Optional formatting templates - override for custom formatting
    human_template: Optional[str] = None
    agent_template: Optional[str] = None
    param_key: Optional[str] = None  # Primary parameter for display

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format tool execution for human display with auto-generation."""
        param_str = self._format_params(params)

        if results is None:
            return param_str, ""

        if results.failure:
            return param_str, f"Error: {results.error}"

        # Use template if provided, otherwise auto-generate
        if self.human_template:
            try:
                result_str = self.human_template.format(**results.data)
            except (KeyError, ValueError):
                result_str = self._format_result(results.data)
        else:
            result_str = self._format_result(results.data)

        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format tool results for agent action history with auto-generation."""
        if not result_data:
            return "No result"

        # Use template if provided, otherwise auto-generate
        if self.agent_template:
            try:
                return self.agent_template.format(**result_data)
            except (KeyError, ValueError):
                return self._format_result(result_data)
        else:
            return self._format_result(result_data)

    def _format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display with smart truncation."""
        if not params:
            return ""

        from cogency.utils import truncate

        # Use hint if provided
        if self.param_key and self.param_key in params:
            return f"({truncate(str(params[self.param_key]), 30)})"

        # Auto-detect primary parameter (first non-None value)
        for _key, value in params.items():
            if value is not None:
                return f"({truncate(str(value), 30)})"

        return ""

    def _format_result(self, data: Dict[str, Any]) -> str:
        """Smart default formatting based on common patterns."""
        if not data:
            return "Completed"

        # Common single-value patterns
        if "result" in data:
            return str(data["result"])
        if "message" in data:
            return str(data["message"])
        if "output" in data:
            return str(data["output"])

        # Single key-value pair
        if len(data) == 1:
            key, value = next(iter(data.items()))
            return f"{key}: {value}"

        # Multiple items - show count or summary
        if "count" in data:
            return f"Processed {data['count']} items"

        return f"Completed ({len(data)} results)"
