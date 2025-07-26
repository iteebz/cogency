from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from cogency.types.params import validate
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
        params: Optional[Type] = None,
        examples: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
    ):
        """Initialize the tool with metadata and LLM guidance.

        Args:
            name: The name of the tool (used for tool calls)
            description: Human-readable description of what the tool does
            emoji: Visual emoji for this tool type (defaults to generic 🛠️)
            params: Dataclass for parameter validation
            examples: List of example tool calls for LLM guidance
            rules: List of usage rules and completion guidance
        """
        self.name = name
        self.description = description
        self.emoji = emoji
        self.params = params
        self.examples = examples or []
        self.rules = rules or []

    @property
    def schema(self) -> str:
        """Backward compatibility property that generates schema from dataclass."""
        if not self.params:
            return f"{self.name}() - No parameters required"
        
        # Generate schema string from dataclass fields
        import inspect
        from dataclasses import fields, is_dataclass
        
        if not is_dataclass(self.params):
            return f"{self.name}() - Parameters not defined as dataclass"
        
        param_strs = []
        required = []
        optional = []
        
        from dataclasses import MISSING
        
        for field in fields(self.params):
            field_type = field.type
            has_default = field.default is not MISSING or field.default_factory is not MISSING
            
            # Check if Optional type (Union with None)
            import typing
            is_optional = (hasattr(field_type, '__origin__') and 
                          field_type.__origin__ is typing.Union and
                          type(None) in field_type.__args__)
            
            if has_default or is_optional:
                optional.append(field.name)
            else:
                required.append(field.name)
            
            # Add to param strings
            if field.default is not MISSING:
                param_strs.append(f"{field.name}={repr(field.default)}")
            else:
                param_strs.append(f"{field.name}='...'")
        
        param_str = ", ".join(param_strs)
        req_str = "Required: " + ", ".join(required) if required else ""
        opt_str = "Optional: " + ", ".join(optional) if optional else ""
        
        parts = [f"{self.name}({param_str})"]
        if req_str and opt_str:
            parts.append(f"{req_str} | {opt_str}")
        elif req_str:
            parts.append(req_str)
        elif opt_str:
            parts.append(opt_str)
        
        return "\n".join(parts)

    async def execute(self, **kwargs: Any) -> ToolResult:
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
            return ToolResult.fail(f"Invalid parameters: {str(e)}")
        except Exception as e:
            return ToolResult.fail(f"Tool execution failed: {str(e)}")

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given parameters.

        Returns:
            Dict containing the tool's results or error information
        """
        pass

    @abstractmethod
    def format_human(
        self, params: Dict[str, Any], results: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """Format tool execution for human display."""
        pass

    @abstractmethod
    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format tool results for agent action history - show knowledge gained."""
        pass
