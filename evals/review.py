"""Human review queue and validation pipeline."""

import json
import random
from pathlib import Path
from typing import Any, Optional

from cogency.config.paths import paths


class HumanReviewQueue:
    """Manage human validation workflow."""

    def __init__(self):
        self.queue_dir = Path(paths.evals) / "human_review_queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)

        self.completed_dir = self.queue_dir / "completed"
        self.completed_dir.mkdir(exist_ok=True)

    def should_review(self, judge_confidence: float, is_regression: bool = False) -> bool:
        """Determine if result should be queued for human review."""
        return (
            judge_confidence < 0.7  # Low confidence trigger
            or is_regression  # Regression detection trigger
            or random.random() < 0.1  # 10% random sample
        )

    def queue_for_review(
        self,
        test_case: str,
        agent_response: str,
        judge_score: float,
        judge_reasoning: str,
        judge_confidence: float,
        metadata: dict[str, Any],
    ) -> str:
        """Add item to human review queue."""

        review_id = f"review_{len(list(self.queue_dir.glob('*.json')))}"

        review_item = {
            "id": review_id,
            "test_case": test_case,
            "agent_response": agent_response,
            "judge_evaluation": {
                "score": judge_score,
                "confidence": judge_confidence,
                "reasoning": judge_reasoning,
            },
            "metadata": metadata,
            "human_evaluation": {"score": None, "notes": None, "reviewer": None, "timestamp": None},
            "status": "pending",
        }

        queue_file = self.queue_dir / f"{review_id}.json"
        with open(queue_file, "w") as f:
            json.dump(review_item, f, indent=2)

        return review_id

    def get_pending_reviews(self) -> list[dict[str, Any]]:
        """Get all pending human reviews."""
        pending = []

        for review_file in self.queue_dir.glob("*.json"):
            with open(review_file) as f:
                review_item = json.load(f)

            if review_item.get("status") == "pending":
                pending.append(review_item)

        return sorted(pending, key=lambda x: x["id"])

    def complete_review(
        self, review_id: str, human_score: float, human_notes: str, reviewer: str
    ) -> bool:
        """Mark review as completed with human evaluation."""

        review_file = self.queue_dir / f"{review_id}.json"
        if not review_file.exists():
            return False

        with open(review_file) as f:
            review_item = json.load(f)

        # Update with human evaluation
        review_item["human_evaluation"] = {
            "score": human_score,
            "notes": human_notes,
            "reviewer": reviewer,
            "timestamp": json.dumps({"timestamp": "now"}),  # Simplified for demo
        }
        review_item["status"] = "completed"

        # Move to completed directory
        completed_file = self.completed_dir / f"{review_id}.json"
        with open(completed_file, "w") as f:
            json.dump(review_item, f, indent=2)

        # Remove from queue
        review_file.unlink()

        return True

    def get_judge_accuracy(self) -> Optional[dict[str, float]]:
        """Calculate LLM judge accuracy against human reviews."""
        completed_reviews = []

        for completed_file in self.completed_dir.glob("*.json"):
            with open(completed_file) as f:
                review = json.load(f)

            human_score = review["human_evaluation"].get("score")
            judge_score = review["judge_evaluation"]["score"]

            if human_score is not None:
                completed_reviews.append(
                    {
                        "human_score": human_score,
                        "judge_score": judge_score,
                        "difference": abs(human_score - judge_score),
                    }
                )

        if not completed_reviews:
            return None

        # Calculate accuracy metrics
        differences = [r["difference"] for r in completed_reviews]
        avg_difference = sum(differences) / len(differences)

        # Consider "accurate" if within 1 point
        accurate_count = sum(1 for d in differences if d <= 1.0)
        accuracy_rate = accurate_count / len(differences)

        return {
            "total_reviews": len(completed_reviews),
            "average_difference": round(avg_difference, 2),
            "accuracy_rate": round(accuracy_rate, 3),
            "within_1_point": accurate_count,
        }
