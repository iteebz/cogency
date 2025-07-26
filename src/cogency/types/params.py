"""Dataclass-based parameter validation for tools."""

from dataclasses import dataclass
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


def validate(params: Dict[str, Any], params_class: Type[T]) -> T:
    """Validate and convert dict parameters to dataclass instance.

    Args:
        params: Raw parameters from tool call
        params_class: Dataclass type to validate against

    Returns:
        Validated dataclass instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return params_class(**params)
    except TypeError as e:
        # Convert TypeError to ValueError for consistent error handling
        raise ValueError(f"Invalid parameters: {str(e)}") from e


# Base class for tool parameters (optional - tools can use plain dataclasses)
@dataclass
class BaseParams:
    """Base class for tool parameter validation."""

    def __post_init__(self):
        """Override in subclasses for custom validation logic."""
        pass
