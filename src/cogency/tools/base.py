"""Base tool interface - standardized execution, validation, and formatting."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from resilient_result import Result

# Metrics removed - agent observability handled by event system
from cogency.utils.validation import validate


class Tool(ABC):
    """Base class for all tools in the cogency framework.

    Standardized tool interface requiring:
    - name, description, emoji: Tool identification
    - schema, examples, rules: LLM guidance (strings/lists in init)
    - run(): Core execution logic
    - format(): Display formatting for args and results
    """

    def __init__(
        self,
        name: str,
        description: str,
        schema: str,
        emoji: str = "🛠️",
        args: Optional[Type] = None,
        examples: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
    ):
        """Initialize tool with metadata and LLM guidance.

        Args:
            name: Tool name for LLM calls
            description: What the tool does
            schema: LLM schema string (e.g. "code(expression='2+2')")
            emoji: Visual identifier (default: 🛠️)
            args: Dataclass for validation
            examples: Example calls for LLM
            rules: Usage rules and guidance
        """
        self.name = name
        self.description = description
        self.schema = schema
        self.emoji = emoji
        self.args = args
        self.examples = examples or []
        self.rules = rules or []

    # Schema is now explicit - no ceremony, just clean strings

    async def execute(self, **kwargs: Any) -> Result:
        """Execute tool with validation and error handling.

        Use this method instead of run() directly.
        """
        import time

        from cogency.events import emit

        start_time = time.time()
        emit("tool", operation="execute", name=self.name, status="start")

        try:
            # Normalize and validate arguments
            normalized_args = self._normalize_args(kwargs)

            # Validate args using dataclass schema if provided
            if self.args:
                validated_args = validate(normalized_args, self.args)
                result = await self.run(**validated_args.__dict__)
            else:
                # Direct execution if no schema
                result = await self.run(**normalized_args)

            # Auto-wrap non-Result returns for better DX
            if not hasattr(result, "failure"):
                result = Result.ok(result)

            # Track events only - metrics handled by MetricsHandler
            duration = time.time() - start_time
            if result.failure:
                emit(
                    "tool",
                    operation="execute",
                    name=self.name,
                    status="failed",
                    error=result.error,
                    duration=duration,
                )
            else:
                emit(
                    "tool",
                    operation="execute",
                    name=self.name,
                    status="complete",
                    success=True,
                    duration=duration,
                )

            return result

        except ValueError as e:
            # Schema validation errors
            duration = time.time() - start_time
            emit(
                "tool",
                operation="execute",
                name=self.name,
                status="validation_error",
                error=str(e),
                duration=duration,
            )
            return Result.fail(f"Invalid arguments: {str(e)}")
        except Exception as e:
            # Critical execution errors
            duration = time.time() - start_time
            emit(
                "tool",
                operation="execute",
                name=self.name,
                status="execution_error",
                error=str(e),
                duration=duration,
            )
            return Result.fail(f"Tool execution failed: {str(e)}")

    def _normalize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Basic argument normalization."""
        return args

    @abstractmethod
    async def run(self, **kwargs: Any) -> Result:
        """Execute the tool with given arguments.

        Returns:
            Result containing tool output or error
        """
        pass

    # Optional formatting templates - override for custom formatting
    human_template: Optional[str] = None
    agent_template: Optional[str] = None
    arg_key: Optional[str] = None  # Primary argument for display

    def format_human(
        self, args: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format tool execution for human display."""
        arg_str = self._format_args(args)

        if results is None:
            return arg_str, ""

        if results.failure:
            return arg_str, f"Error: {results.error}"

        # Use template if provided, otherwise auto-generate
        if self.human_template:
            try:
                result_str = self.human_template.format(**results.data)
            except (KeyError, ValueError):
                result_str = self._format_result(results.data)
        else:
            result_str = self._format_result(results.data)

        return arg_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format tool results for agent action history."""
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

    def _format_args(self, args: Dict[str, Any]) -> str:
        """Format arguments for display."""
        if not args:
            return ""

        def _truncate(text: str, length: int) -> str:
            return text if len(text) <= length else text[: length - 3] + "..."

        # Use hint if provided
        if self.arg_key and self.arg_key in args:
            return f"({_truncate(str(args[self.arg_key]), 30)})"

        # Auto-detect primary argument (first non-None value)
        for _key, value in args.items():
            if value is not None:
                return f"({_truncate(str(value), 30)})"

        return ""

    def _format_result(self, data: Dict[str, Any]) -> str:
        """Format result data."""
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
