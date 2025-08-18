"""Canonical Result type with autoflattening constructors.

Beautiful error handling that flows through the system naturally.
Single unwrap boundary at final consumption points.
"""

from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """Result type for success and failure cases with autoflattening flow."""

    def __init__(self, data: T = None, error: E = None):
        self._data = data
        self._error = error

    @property
    def success(self) -> bool:
        """True if result is successful."""
        return self._error is None

    @property
    def failure(self) -> bool:
        """True if result failed."""
        return self._error is not None

    @property
    def error(self) -> E:
        """Error value for inspection."""
        return self._error

    def unwrap(self) -> T:
        """Extract data, raising exception if failed.

        Single boundary discipline - only unwrap at final consumption.
        """
        if self.failure:
            raise ValueError(f"Cannot unwrap failed result: {self._error}")
        return self._data

    def __bool__(self) -> bool:
        """Allow `if result:` checks."""
        return self.success

    def __repr__(self) -> str:
        if self.success:
            return f"Ok({repr(self._data)})"
        return f"Err({repr(self._error)})"


def Ok(data: T = None) -> Result[T, E]:  # noqa: N802
    """Create successful result with autoflattening.

    Autoflattening prevents nested Result states:
    Ok(Ok("data")) → Ok("data")
    Ok(Err("error")) → Err("error")
    """
    if isinstance(data, Result):
        return data  # Pass through - no nesting
    return Result(data=data)


def Err(error: E) -> Result[T, E]:  # noqa: N802
    """Create failed result with autoflattening.

    Autoflattening prevents nested Result states:
    Err(Err("error")) → Err("error")
    """
    if isinstance(error, Result) and error.failure:
        return error  # Pass through failed Result
        # If it's a successful Result, keep it as the error data
    return Result(error=error)
