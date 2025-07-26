"""Resilience utilities for clean Result handling."""

from typing import Any


def smart_unwrap(obj: Any) -> Any:
    """Smart Result unwrapping - clean boundary discipline helper.

    Unwraps Result objects when needed, passes through everything else.
    Use inside decorated functions where boundary discipline requires manual unwrapping.
    """
    if hasattr(obj, "success") and hasattr(obj, "data") and hasattr(obj, "error"):
        # This is a Result object - unwrap it
        if not obj.success:
            error = obj.error
            if isinstance(error, str):
                raise ValueError(error)
            raise error
        return obj.data

    # Not a Result object - pass through
    return obj
