"""Evaluation execution engine."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from resilient_result import Result

from cogency.observe import simple_timer

from .models import EvalResult, FailureType
from .report import EvalReport

# Global notification collector for eval runs
_eval_notifications = []


async def _capture_notification(notification):
    """Capture notifications during eval runs."""
    _eval_notifications.append(
        {"type": notification.type, "data": notification.data, "timestamp": notification.timestamp}
    )


def get_eval_notification_callback():
    """Get notification callback for injecting into agents during evals."""
    return _capture_notification


class Eval(ABC):
    """Base class for all evaluations."""

    name: str = "unnamed_eval"
    description: str = "No description"

    def __init__(self):
        self._timer = None

    @abstractmethod
    async def run(self) -> EvalResult:
        """Execute the evaluation and return results."""
        pass

    def check(self, actual: Any, expected: Any, metadata: Optional[Dict] = None) -> EvalResult:
        """Helper to create EvalResult from comparison."""
        passed = actual == expected
        score = 1.0 if passed else 0.0
        duration = self._timer() if self._timer else 0.0

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
        duration = self._timer() if self._timer else 0.0

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
        self._timer = simple_timer(f"eval_{self.name}")

        try:
            result = await self.run()
            return Result.ok(result)
        except Exception as e:
            error_result = self.fail(f"{type(e).__name__}: {e}")
            return Result.ok(error_result)


async def run_suite(eval_classes: List[type[Eval]], sequential: bool = False) -> EvalReport:
    """Run multiple evaluations in parallel or sequential mode."""
    if not eval_classes:
        return EvalReport([])

    # Clear notification capture for fresh run
    global _eval_notifications
    _eval_notifications.clear()

    results = (
        await _run_sequential(eval_classes) if sequential else await _run_parallel(eval_classes)
    )

    # Create report with captured notifications
    report = EvalReport(results)
    report.notifications = _eval_notifications.copy()
    return report


async def _run_sequential(eval_classes: List[type[Eval]]) -> List[EvalResult]:
    """Sequential execution for rate-limited environments."""
    results = []
    for eval_class in eval_classes:
        task_result = await eval_class().execute()
        results.append(_extract_result(task_result))
        await asyncio.sleep(0.5)  # Rate limit buffer
    return results


async def _run_parallel(eval_classes: List[type[Eval]]) -> List[EvalResult]:
    """Parallel execution (default)."""
    tasks = [eval_class().execute() for eval_class in eval_classes]
    task_results = await asyncio.gather(*tasks)
    return [_extract_result(task_result) for task_result in task_results]


def _extract_result(task_result) -> EvalResult:
    """Extract EvalResult from task result."""
    if task_result.is_ok():
        return task_result.unwrap()
    return EvalResult(
        name="unknown",
        passed=False,
        score=0.0,
        duration=0.0,
        error=task_result.unwrap_err(),
        failure_type=FailureType.ERROR,
    )
