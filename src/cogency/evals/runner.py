"""Eval runner - execute single evals or suites with beautiful reports."""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from .base import Eval, EvalResult


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
            return "X No evals found"

        status = "✓" if self.passed == self.total else "X"

        lines = [
            f"{status} Evals: {self.passed}/{self.total} passed",
            f"  Score: {self.score:.1%}",
            f"  Duration: {self.duration:.2f}s",
            "",
        ]

        for result in self.results:
            status = "✓" if result.passed else "X"
            lines.append(f"{status} {result.name} ({result.duration:.2f}s)")
            if result.error:
                lines.append(f"   ERROR: {result.error}")

        return "\n".join(lines)


async def run_eval(eval_class: type[Eval], output_dir: Optional[Path] = None) -> EvalReport:
    """Run a single evaluation."""
    eval_instance = eval_class()
    result = await eval_instance.execute()

    if result.is_err():
        # This shouldn't happen with current implementation, but just in case
        failed_result = EvalResult(
            name=eval_instance.name,
            passed=False,
            score=0.0,
            duration=0.0,
            error=result.unwrap_err(),
        )
        results = [failed_result]
    else:
        results = [result.unwrap()]

    report = EvalReport(results)

    if output_dir:
        await _save_report(report, output_dir, eval_instance.name)

    return report


async def run_suite(
    eval_classes: List[type[Eval]], output_dir: Optional[Path] = None
) -> EvalReport:
    """Run multiple evaluations in parallel."""
    if not eval_classes:
        return EvalReport([])

    # Run all evals in parallel for speed
    tasks = [eval_class().execute() for eval_class in eval_classes]
    results = await asyncio.gather(*tasks)

    # Convert Results to EvalResults
    eval_results = []
    for i, result in enumerate(results):
        if result.is_err():
            # Shouldn't happen, but handle gracefully
            failed_result = EvalResult(
                name=eval_classes[i]().name,
                passed=False,
                score=0.0,
                duration=0.0,
                error=result.unwrap_err(),
            )
            eval_results.append(failed_result)
        else:
            eval_results.append(result.unwrap())

    report = EvalReport(eval_results)

    if output_dir:
        await _save_report(report, output_dir, "suite")

    return report


async def _save_report(report: EvalReport, output_dir: Path, name: str) -> None:
    """Save report to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    filename = f"{name}_{timestamp}.json"
    filepath = output_dir / filename

    with open(filepath, "w") as f:
        json.dump(report.json(), f, indent=2)

    print(f"Report saved: {filepath}")
