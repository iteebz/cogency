"""Evaluation suite execution."""

import asyncio
import time
from typing import List

from .context import AgentRobustContext
from .eval import Eval
from .models import EvalResult, FailureType
from .notifications import clear, get_all
from .report import EvalReport


async def run_suite(
    eval_classes: List[type[Eval]], sequential: bool = False, robust: bool = False
) -> EvalReport:
    """Run evaluation suite.

    Args:
        eval_classes: List of Eval classes to run
        sequential: Run sequentially instead of parallel
        robust: Enable robust mode for agents

    Returns:
        EvalReport with results and notifications
    """
    if not eval_classes:
        return EvalReport([])

    # Clear notification capture for fresh run
    clear()

    # Run evals with robust context if requested
    with AgentRobustContext(robust):
        results = (
            await _run_sequential(eval_classes) if sequential else await _run_parallel(eval_classes)
        )

    # Create report with captured notifications
    report = EvalReport(results)
    report.notifications = get_all()
    return report


async def _run_sequential(eval_classes: List[type[Eval]]) -> List[EvalResult]:
    """Run evaluations sequentially."""
    results = []
    total = len(eval_classes)

    for i, eval_class in enumerate(eval_classes, 1):
        eval_name = getattr(eval_class, "name", eval_class.__name__)

        # Show eval header
        print(f"[{i}/{total}] {eval_name}", flush=True)

        start_time = time.time()
        task_result = await eval_class().execute()
        result = _extract_result(task_result)
        results.append(result)

        # If no sub-cases were shown, show simple result
        if not result.sub_cases:
            duration = time.time() - start_time
            status = "✓" if result.passed else "✗"
            print(f"  {status} Single test ({duration:.1f}s)", flush=True)

        await asyncio.sleep(0.5)  # Rate limit buffer
    return results


async def _run_parallel(eval_classes: List[type[Eval]]) -> List[EvalResult]:
    """Run evaluations in parallel."""
    tasks = [eval_class().execute() for eval_class in eval_classes]
    task_results = await asyncio.gather(*tasks)
    return [_extract_result(task_result) for task_result in task_results]


def _extract_result(task_result) -> EvalResult:
    """Extract EvalResult from task."""
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
