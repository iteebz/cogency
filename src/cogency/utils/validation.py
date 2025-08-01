"""Input validation utilities."""

from typing import Any, Dict, Type, TypeVar

MAX_QUERY_LENGTH = 10000

T = TypeVar("T")


def validate_query(query: str) -> str | None:
    """Validate query input, return error message if invalid."""
    if not query or not query.strip():
        return "⚠️ Empty query not allowed"

    if len(query) > MAX_QUERY_LENGTH:
        return f"⚠️ Query too long (max {MAX_QUERY_LENGTH:,} characters)"

    return None


def validate(params: Dict[str, Any], schema: Type[T]) -> T:
    """Validate parameters against dataclass schema.

    Args:
        params: Dictionary of parameters to validate
        schema: Dataclass type to validate against

    Returns:
        Validated dataclass instance

    Raises:
        ValueError: If validation fails
    """
    if not hasattr(schema, "__dataclass_fields__"):
        raise ValueError(f"Schema {schema} is not a dataclass")

    try:
        return schema(**params)
    except TypeError as e:
        raise ValueError(f"Parameter validation failed: {str(e)}") from e
