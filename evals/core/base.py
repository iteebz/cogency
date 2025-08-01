"""Base evaluation class - Tool-like interface for testing agents."""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel
from resilient_result import Result


class EvalResult(BaseModel):
    """Result of running an evaluation."""

    name: str
    passed: bool
    score: float  # 0.0 to 1.0
    duration: float  # seconds
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class Eval(ABC):
    """Base class for all evaluations.

    Simple, Tool-like interface for testing agent capabilities.
    """

    name: str = "unnamed_eval"
    description: str = "No description"

    def __init__(self):
        self.start_time: Optional[float] = None

    @abstractmethod
    async def run(self) -> EvalResult:
        """Execute the evaluation and return results."""
        pass

    def check(self, actual: Any, expected: Any, metadata: Optional[Dict] = None) -> EvalResult:
        """Helper to create EvalResult from comparison."""
        passed = actual == expected
        score = 1.0 if passed else 0.0
        duration = time.time() - (self.start_time or time.time())

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=duration,
            expected=expected,
            actual=actual,
            metadata=metadata or {},
        )

    def fail(self, error: str, metadata: Optional[Dict] = None) -> EvalResult:
        """Helper to create failed EvalResult."""
        duration = time.time() - (self.start_time or time.time())

        return EvalResult(
            name=self.name,
            passed=False,
            score=0.0,
            duration=duration,
            error=error,
            metadata=metadata or {},
        )

    async def execute(self) -> Result[EvalResult, str]:
        """Execute eval with error handling."""
        self.start_time = time.time()

        try:
            result = await self.run()
            return Result.ok(result)
        except Exception as e:
            error_result = self.fail(f"{type(e).__name__}: {e}")
            return Result.ok(error_result)  # Don't fail the runner, just mark eval as failed
