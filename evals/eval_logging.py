"""Raw output logging with full metadata capture."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from cogency.config.paths import paths

from .judges.scoring import JudgeResult


class EvalLogger:
    """Comprehensive evaluation logging system."""

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = Path(paths.evals) / "runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Create canonical subdirectories
        (self.run_dir / "raw").mkdir(exist_ok=True)
        (self.run_dir / "review").mkdir(exist_ok=True)

        self.results: list[dict[str, Any]] = []
        self.test_counters: dict[str, int] = {}

    def log_result(
        self,
        eval_name: str,
        judge_result: JudgeResult,
        agent_metadata: dict[str, Any],
        execution_time: float,
    ) -> None:
        """Log complete evaluation result with full metadata."""

        timestamp = datetime.now().isoformat()

        # Complete result record
        record = {
            "timestamp": timestamp,
            "run_id": self.run_id,
            "eval_name": eval_name,
            "test_case": judge_result.test_case,
            "agent_response": judge_result.agent_response,
            "judge_result": asdict(judge_result.score),
            "judge_model": judge_result.judge_model,
            "agent_metadata": agent_metadata,
            "execution_time": execution_time,
            "needs_human_review": judge_result.needs_human_review,
        }

        self.results.append(record)

        # Generate canonical filename with sequential numbering
        eval_type = self._extract_eval_type(eval_name)
        self.test_counters[eval_type] = self.test_counters.get(eval_type, 0) + 1
        test_num = self.test_counters[eval_type]

        raw_file = self.run_dir / "raw" / f"{eval_type}_{test_num:03d}.json"
        with open(raw_file, "w") as f:
            json.dump(record, f, indent=2)

        # Queue for human review if needed
        if judge_result.needs_human_review:
            self._queue_human_review(record)

    def _queue_human_review(self, record: dict[str, Any]) -> None:
        """Queue result for human validation."""
        eval_type = self._extract_eval_type(record["eval_name"])
        test_num = self.test_counters[eval_type]
        review_file = self.run_dir / "review" / f"{eval_type}_{test_num:03d}.json"

        # Simplified record for human reviewers
        review_record = {
            "test_case": record["test_case"],
            "agent_response": record["agent_response"],
            "judge_score": record["judge_result"]["value"],
            "judge_reasoning": record["judge_result"]["reasoning"],
            "judge_confidence": record["judge_result"]["confidence"],
            "human_score": None,  # To be filled by reviewer
            "human_notes": None,  # To be filled by reviewer
            "timestamp": record["timestamp"],
        }

        with open(review_file, "w") as f:
            json.dump(review_record, f, indent=2)

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive evaluation report."""
        if not self.results:
            return {"error": "No results to report"}

        scores = [r["judge_result"]["value"] for r in self.results]
        confidences = [r["judge_result"]["confidence"] for r in self.results]
        execution_times = [r["execution_time"] for r in self.results]

        # Calculate statistics
        avg_score = sum(scores) / len(scores)
        avg_confidence = sum(confidences) / len(confidences)
        avg_execution_time = sum(execution_times) / len(execution_times)

        low_confidence_count = sum(1 for c in confidences if c < 0.7)
        poor_performance_count = sum(1 for s in scores if s <= 3.0)
        human_review_count = sum(1 for r in self.results if r["needs_human_review"])

        report = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "total_evaluations": len(self.results),
            "statistics": {
                "average_score": round(avg_score, 2),
                "average_confidence": round(avg_confidence, 3),
                "average_execution_time": round(avg_execution_time, 2),
                "score_range": [min(scores), max(scores)],
                "confidence_range": [min(confidences), max(confidences)],
            },
            "quality_indicators": {
                "low_confidence_results": low_confidence_count,
                "poor_performance_results": poor_performance_count,
                "human_review_queued": human_review_count,
            },
            "breakdown_by_eval": self._breakdown_by_eval(),
        }

        # Save canonical report
        report_file = self.run_dir / "results.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Create latest symlink
        self._create_latest_symlink()

        return report

    def _breakdown_by_eval(self) -> dict[str, dict[str, Any]]:
        """Break down results by evaluation name."""
        breakdown = {}

        for result in self.results:
            eval_name = result["eval_name"]
            if eval_name not in breakdown:
                breakdown[eval_name] = {
                    "count": 0,
                    "scores": [],
                    "confidences": [],
                    "execution_times": [],
                }

            breakdown[eval_name]["count"] += 1
            breakdown[eval_name]["scores"].append(result["judge_result"]["value"])
            breakdown[eval_name]["confidences"].append(result["judge_result"]["confidence"])
            breakdown[eval_name]["execution_times"].append(result["execution_time"])

        # Calculate averages
        for _eval_name, data in breakdown.items():
            data["average_score"] = round(sum(data["scores"]) / len(data["scores"]), 2)
            data["average_confidence"] = round(
                sum(data["confidences"]) / len(data["confidences"]), 3
            )
            data["average_execution_time"] = round(
                sum(data["execution_times"]) / len(data["execution_times"]), 2
            )

        return breakdown

    def _extract_eval_type(self, eval_name: str) -> str:
        """Extract clean eval type from verbose eval name."""
        # Remove common prefixes and suffixes, extract core type
        name = eval_name.lower()

        if "security" in name or "injection" in name:
            return "security"
        if "memory" in name:
            if "cross" in name:
                return "memory_cross_session"
            return "memory"
        if "tool" in name:
            return "tools"
        if "network" in name or "resilience" in name:
            return "network"
        if "reasoning" in name or "reason" in name:
            return "reasoning"
        # Fallback: take first meaningful word
        parts = name.replace("_", " ").split()
        return parts[0] if parts else "unknown"

    def _create_latest_symlink(self) -> None:
        """Create symlink to latest run for easy access."""
        try:
            latest_link = self.run_dir.parent / "latest"
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(self.run_dir.name)
        except Exception:
            # Symlinks may fail on some filesystems, ignore silently
            pass
