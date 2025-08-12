"""TEMPORARY: Gemini self-evaluation judge (VIOLATION - for development only).

TODO: Replace with proper multi-model evaluation once Gemini agents are working.
This violates the "never self-evaluate" principle but enables measurement now.
"""

from dataclasses import dataclass
from typing import Any, Optional

from .scoring import JudgeResult, Score


@dataclass
class GeminiJudge:
    """TEMPORARY Gemini self-evaluation judge."""

    model_name: str = "gemini-2.0-flash-exp"

    async def evaluate(
        self,
        agent_response: str,
        test_case: str,
        criteria: str,
        context: Optional[dict[str, Any]] = None,
    ) -> JudgeResult:
        """Evaluate using Gemini (TEMPORARY SELF-EVALUATION)."""

        # TODO: Replace this with proper multi-model evaluation
        # For now, use Gemini to judge Gemini responses
        from cogency.providers.gemini import Gemini

        judge_llm = Gemini()

        evaluation_prompt = f"""You are an evaluation judge assessing an AI agent's performance.

**Test Case:** {test_case}

**Agent Response:** {agent_response}

**Evaluation Criteria:** {criteria}

Please provide:
1. A score from 1-10 (10 being excellent)
2. Confidence level (0.0 to 1.0) in your assessment
3. Brief reasoning for the score

Format your response as:
SCORE: [1-10]
CONFIDENCE: [0.0-1.0]
REASONING: [Your explanation]"""

        try:
            judge_response = await judge_llm.generate(
                system_prompt="You are an impartial evaluation judge. Provide accurate, consistent scoring.",
                user_message=evaluation_prompt,
            )

            # Parse the structured response
            score_value = self._extract_score(judge_response)
            confidence = self._extract_confidence(judge_response)
            reasoning = self._extract_reasoning(judge_response)

            score = Score(value=score_value, confidence=confidence, reasoning=reasoning)

            return JudgeResult(
                score=score,
                judge_model="gemini-2.0-flash-exp-SELF-EVAL-VIOLATION",
                test_case=test_case,
                agent_response=agent_response,
                context=context or {},
            )

        except Exception as e:
            # Fallback scoring on error
            return JudgeResult(
                score=Score(
                    value=5.0,  # Neutral score
                    confidence=0.1,  # Low confidence
                    reasoning=f"Judge evaluation failed: {str(e)}",
                ),
                judge_model="gemini-2.0-flash-exp-ERROR",
                test_case=test_case,
                agent_response=agent_response,
                context=context or {},
            )

    def _extract_score(self, response: str) -> float:
        """Extract score from judge response."""
        lines = response.split("\n")
        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score_str = line.replace("SCORE:", "").strip()
                    return float(score_str)
                except ValueError:
                    pass

        # Fallback: look for any number 1-10
        import re

        numbers = re.findall(r"\b([1-9]|10)\b", response)
        if numbers:
            return float(numbers[0])

        return 5.0  # Default neutral score

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence from judge response."""
        lines = response.split("\n")
        for line in lines:
            if line.startswith("CONFIDENCE:"):
                try:
                    conf_str = line.replace("CONFIDENCE:", "").strip()
                    confidence = float(conf_str)
                    return max(0.0, min(1.0, confidence))  # Clamp to [0,1]
                except ValueError:
                    pass

        return 0.5  # Default medium confidence

    def _extract_reasoning(self, response: str) -> str:
        """Extract reasoning from judge response."""
        lines = response.split("\n")
        reasoning_started = False
        reasoning_lines = []

        for line in lines:
            if line.startswith("REASONING:"):
                reasoning_started = True
                reasoning_lines.append(line.replace("REASONING:", "").strip())
            elif reasoning_started:
                reasoning_lines.append(line.strip())

        reasoning = " ".join(reasoning_lines).strip()
        return reasoning if reasoning else "No reasoning provided"
