"""Evaluation reporting and storage."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List

from cogency.config import PathsConfig

from .models import EvalResult, FailureType


class EvalJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for eval objects."""

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)


class EvalReport:
    """Generate eval reports."""

    def __init__(self, results: List[EvalResult]):
        self.results = results
        self.passed = sum(1 for r in results if r.passed)
        self.total = len(results)
        self.score = sum(r.score for r in results) / self.total if self.total > 0 else 0.0
        self.duration = sum(r.duration for r in results)
        self.notifications = []  # Will be populated by runner

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
            "notifications": self.notifications,
        }

    def console(self) -> str:
        """Console output."""
        if self.total == 0:
            return "✗ No evals found"

        status = "✓" if self.passed == self.total else "✗"
        lines = [
            f"Evals: {self.passed}/{self.total} passed",
            f"Score: {self.score:.1%}",
            f"Duration: {self.duration:.2f}s",
        ]

        for result in self.results:
            status = "✓" if result.passed else "✗"
            score_pct = f"{result.score:.0%}"
            lines.append(f"{status} {score_pct} • {result.name} • {result.duration:.2f}s")
            if result.error:
                lines.append(f"   ERROR: {result.error}")

        return "\n".join(lines)

    def _format_failure(self, result: EvalResult) -> str:
        """Format failure indicators."""
        if result.passed or not result.failure_type:
            return ""

        icons = {
            FailureType.LOGIC: "❌",
            FailureType.RATE_LIMIT: "⚠️",
            FailureType.TIMEOUT: "⏱️",
            FailureType.ERROR: "🚫",
        }
        icon = icons.get(result.failure_type, "❌")
        text = f" {icon} {result.failure_type.upper()}"
        if result.retries > 0:
            text += f" ({result.retries} retries)"
        return text


async def save_report(report: EvalReport, name: str) -> Path:
    """Save report with bundled artifacts in timestamped run folder."""
    paths = PathsConfig()

    # Create timestamped run folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(paths.evals) / f"{name}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save main report
    report_file = run_dir / "report.json"
    with open(report_file, "w") as f:
        json.dump(report.json(), f, indent=2, cls=EvalJSONEncoder)

    # Save console output for later review
    console_file = run_dir / "console.txt"
    with open(console_file, "w") as f:
        f.write(report.console())

    # Save captured notifications for debugging
    notifications_file = run_dir / "notifications.json"
    with open(notifications_file, "w") as f:
        json.dump(report.notifications, f, indent=2, cls=EvalJSONEncoder)

    # Save metadata about the run
    metadata_file = run_dir / "metadata.json"
    metadata = {
        "suite": name,
        "timestamp": timestamp,
        "total_evals": report.total,
        "passed": report.passed,
        "score": report.score,
        "duration": report.duration,
        "eval_names": [r.name for r in report.results],
    }
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return run_dir
