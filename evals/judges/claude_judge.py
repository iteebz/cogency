"""Claude 3.5 Sonnet judge for evaluating agent responses."""

import json
import re
from typing import Any

from cogency.providers.anthropic import Anthropic

from .scoring import JudgeResult, Score


class ClaudeJudge:
    """Multi-model judge using Claude 3.5 Sonnet."""

    def __init__(self):
        self.judge = Anthropic(model="claude-3-5-sonnet-20241022")
        self.model_name = "claude-3-5-sonnet-judge"

    async def evaluate(
        self, agent_response: str, test_case: str, criteria: str, context: dict[str, Any] = None
    ) -> JudgeResult:
        """Evaluate agent response using Claude judge."""

        judge_prompt = f"""You are evaluating an AI agent's response for quality measurement.

EVALUATION CRITERIA: {criteria}

TEST CASE: {test_case}

AGENT RESPONSE: {agent_response}

CONTEXT: {json.dumps(context or {}, indent=2)}

Rate this response on a scale of 1-10 considering:
- Accuracy and correctness
- Completeness of answer
- Clarity and coherence
- Appropriateness to the task

Provide your evaluation in this exact JSON format:
{{
    "score": <number 1-10>,
    "confidence": <number 0.0-1.0>,
    "reasoning": "<detailed explanation of your scoring>"
}}

Be precise with your scoring. Use the full 1-10 range."""

        try:
            response = await self.judge.generate(
                system="You are a precise, analytical judge for AI evaluation.",
                prompt=judge_prompt,
                temperature=0.1,  # Low temperature for consistent scoring
            )

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in judge response")

            result = json.loads(json_match.group())

            score = Score(
                value=float(result["score"]),
                confidence=float(result["confidence"]),
                reasoning=result["reasoning"],
            )

            return JudgeResult(
                score=score,
                test_case=test_case,
                agent_response=agent_response,
                judge_model=self.model_name,
                metadata=context or {},
            )

        except Exception as e:
            # Fallback for judge failures
            return JudgeResult(
                score=Score(value=1.0, confidence=0.0, reasoning=f"Judge error: {e}"),
                test_case=test_case,
                agent_response=agent_response,
                judge_model=self.model_name,
                metadata={"error": str(e)},
            )
