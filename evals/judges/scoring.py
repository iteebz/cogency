"""Continuous measurement scoring system."""

from dataclasses import dataclass


@dataclass
class Score:
    """Continuous score from 1-10 with confidence."""

    value: float
    confidence: float
    reasoning: str

    def __post_init__(self):
        if not 1.0 <= self.value <= 10.0:
            raise ValueError(f"Score must be 1-10, got {self.value}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")


@dataclass
class JudgeResult:
    """Complete evaluation result from LLM judge."""

    score: Score
    test_case: str
    agent_response: str
    judge_model: str
    metadata: dict

    @property
    def needs_human_review(self) -> bool:
        """Determine if result requires human validation."""
        return (
            self.score.confidence < 0.7  # Low confidence
            or self.score.value <= 3.0  # Poor performance
        )
