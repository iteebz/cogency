"""Perfect Result pattern - concise factories, descriptive properties."""

from typing import Any


class Result:
    """Perfect Result pattern - best of both worlds."""

    def __init__(self, data: Any = None, error: str = None):
        self.data = data
        self.error = error

    @classmethod
    def ok(cls, data: Any = None) -> "Result":
        """Create successful result."""
        return cls(data=data)

    @classmethod
    def fail(cls, error: str) -> "Result":
        """Create failed result."""
        return cls(error=error)

    @property
    def success(self) -> bool:
        """Check if successful."""
        return self.error is None

    @property
    def failure(self) -> bool:
        """Check if failed."""
        return self.error is not None

    def __bool__(self) -> bool:
        """Allow if result: checks."""
        return self.success

    def __repr__(self) -> str:
        if self.success:
            return f"Result.ok({repr(self.data)})"
        else:
            return f"Result.fail({repr(self.error)})"


class ToolResult(Result):
    """Tool-specific result - same perfect pattern."""

    def __repr__(self) -> str:
        if self.success:
            return f"ToolResult.ok({repr(self.data)})"
        else:
            return f"ToolResult.fail({repr(self.error)})"


class ParseResult(Result):
    """Parsing result with fallback support."""

    @classmethod
    def ok_with_error(cls, data: Any, error: str) -> "ParseResult":
        """Create result with data and error (for fallback scenarios)."""
        return cls(data=data, error=error)

    @property
    def success(self) -> bool:
        """Success if we have data, even with error (fallback scenario)."""
        return self.data is not None

    @property
    def failure(self) -> bool:
        """Failure only if no data available."""
        return self.data is None

    def __repr__(self) -> str:
        if self.success:
            return f"ParseResult.ok({repr(self.data)})"
        else:
            return f"ParseResult.fail({repr(self.error)})"


class ActionResult(Result):
    """Action result with stopping reason."""

    def __init__(
        self,
        data: Any = None,
        error: str = None,
        stopping_reason: str = None,
        can_continue: bool = True,
    ):
        super().__init__(data, error)
        self.stopping_reason = stopping_reason
        self.can_continue = can_continue

    def __repr__(self) -> str:
        if self.success:
            return f"ActionResult.ok({repr(self.data)})"
        else:
            return f"ActionResult.fail({repr(self.error)})"


class RecoveryResult(Result):
    """Recovery result with action info."""

    def __init__(
        self,
        data: Any = None,
        error: str = None,
        recovery_action: str = None,
        can_continue: bool = True,
    ):
        super().__init__(data, error)
        self.recovery_action = recovery_action
        self.can_continue = can_continue

    @classmethod
    def ok(cls, data: Any = None, recovery_action: str = None) -> "RecoveryResult":
        """Create successful recovery result."""
        return cls(data=data, recovery_action=recovery_action)

    @classmethod
    def fail(cls, error: str, recovery_action: str = None) -> "RecoveryResult":
        """Create failed recovery result."""
        return cls(error=error, recovery_action=recovery_action)

    def __repr__(self) -> str:
        if self.success:
            return f"RecoveryResult.ok({repr(self.data)}, action={self.recovery_action})"
        else:
            return f"RecoveryResult.fail({repr(self.error)}, action={self.recovery_action})"
