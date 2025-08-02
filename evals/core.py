"""Beautiful eval core - single interface for all cogency evaluations."""

import asyncio
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from resilient_result import Result

from cogency.config import PathsConfig


class FailureType(str, Enum):
    """Classification of evaluation failures."""

    LOGIC = "logic"  # Model wrong answer
    RATE_LIMIT = "rate_limit"  # API quota/throttling
    TIMEOUT = "timeout"  # Network/processing timeout
    ERROR = "error"  # Unexpected exception


class EvalResult(BaseModel):
    """Result of running an evaluation."""

    name: str
    passed: bool
    score: float  # 0.0 to 1.0
    duration: float  # seconds
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    error: Optional[str] = None
    failure_type: Optional[FailureType] = None
    retries: int = 0
    metadata: Dict[str, Any] = {}


class EvalReport:
    """Generate beautiful eval reports."""

    def __init__(self, results: List[EvalResult]):
        self.results = results
        self.passed = sum(1 for r in results if r.passed)
        self.total = len(results)
        self.score = sum(r.score for r in results) / self.total if self.total > 0 else 0.0
        self.duration = sum(r.duration for r in results)

    def json(self) -> Dict:
        """JSON report data."""
        return {
            "summary": {
                "passed": self.passed,
                "total": self.total,
                "score": round(self.score, 3),
                "duration": round(self.duration, 3),
            },
            "results": [r.model_dump() for r in self.results],
        }

    def console(self) -> str:
        """Beautiful console output."""
        if self.total == 0:
            return "✗ No evals found"

        status = "✓" if self.passed == self.total else "✗"

        lines = [
            f"{status} Evals: {self.passed}/{self.total} passed",
            f"  Score: {self.score:.1%}",
            f"  Duration: {self.duration:.2f}s",
            "",
        ]

        for result in self.results:
            status = "✓" if result.passed else "✗"

            # Add failure type indicator for failed evals
            if not result.passed and result.failure_type:
                failure_icons = {
                    FailureType.LOGIC: "❌",
                    FailureType.RATE_LIMIT: "⚠️",
                    FailureType.TIMEOUT: "⏱️",
                    FailureType.ERROR: "🚫",
                }
                icon = failure_icons.get(result.failure_type, "❌")
                failure_text = f" {icon} {result.failure_type.upper()}"
                if result.retries > 0:
                    failure_text += f" ({result.retries} retries)"
            else:
                failure_text = ""

            lines.append(f"{status} {result.name} ({result.duration:.2f}s){failure_text}")
            if result.error:
                lines.append(f"   ERROR: {result.error}")

        return "\n".join(lines)


class Eval(ABC):
    """Base class for all evaluations."""

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
            return Result.ok(error_result)


async def run_suite(eval_classes: List[type[Eval]], sequential: bool = False) -> EvalReport:
    """Run multiple evaluations in parallel or sequential mode."""
    if not eval_classes:
        return EvalReport([])

    if sequential:
        # Sequential execution for rate-limited environments
        results = []
        for eval_class in eval_classes:
            task_result = await eval_class().execute()
            if task_result.is_ok():
                results.append(task_result.unwrap())
            else:
                # This shouldn't happen with current implementation
                failed_result = EvalResult(
                    name="unknown",
                    passed=False,
                    score=0.0,
                    duration=0.0,
                    error=task_result.unwrap_err(),
                    failure_type=FailureType.ERROR,
                )
                results.append(failed_result)

            # Rate limit buffer between evals
            await asyncio.sleep(0.5)

        return EvalReport(results)

    # Parallel execution (default)
    tasks = [eval_class().execute() for eval_class in eval_classes]
    task_results = await asyncio.gather(*tasks)

    # Extract results
    results = []
    for task_result in task_results:
        if task_result.is_ok():
            results.append(task_result.unwrap())
        else:
            # This shouldn't happen with current implementation
            failed_result = EvalResult(
                name="unknown",
                passed=False,
                score=0.0,
                duration=0.0,
                error=task_result.unwrap_err(),
                failure_type=FailureType.ERROR,
            )
            results.append(failed_result)

    return EvalReport(results)


async def save_report(report: EvalReport, name: str) -> Path:
    """Save report to evals directory."""
    paths = PathsConfig()
    output_dir = Path(paths.evals) / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / f"{name}_{int(time.time())}.json"

    with open(report_file, "w") as f:
        import json

        json.dump(report.json(), f, indent=2)

    return report_file
