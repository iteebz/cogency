"""LLM judge. Headless, gated, runs only after mechanical assertions pass."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .harness import Run

JUDGE_MODEL = "claude-sonnet-4-5"
JUDGE_RETRIES = 3
JUDGE_LOW_CONFIDENCE_THRESHOLD = 0.6


@dataclass
class Score:
    """Judge score."""

    passed: bool
    reasons: list[str]
    confidence: float


async def judge(run: Run, rubric: str, retries: int = JUDGE_RETRIES) -> Score:
    """Judge behavioral case using Claude CLI with retry on low confidence.

    Only called when:
    1. All mechanical assertions pass
    2. Case has rubric
    3. --judge flag is set

    Retries on:
    - Low confidence scores (< threshold)
    - Transient errors
    """
    responds = [e for e in run.events if e.get("type") == "respond"]
    final_response = "".join(e.get("content", "") for e in responds)

    tool_calls = []
    for e in run.events:
        if e.get("type") == "call":
            try:
                parsed = json.loads(e.get("content", "{}"))
                tool_calls.append(f"- {parsed.get('name', 'unknown')}")
            except json.JSONDecodeError:
                tool_calls.append("- (parse error)")

    tool_summary = "\n".join(tool_calls) if tool_calls else "(none)"

    prompt = f"""You are evaluating an AI agent's response. Be strict but fair.

RUBRIC:
{rubric}

TOOLS CALLED:
{tool_summary}

AGENT RESPONSE:
{final_response[:3000]}

INSTRUCTIONS:
1. Evaluate against the rubric criteria only
2. Consider both what was done and how well it was done
3. A PASS requires meeting all rubric requirements
4. Be specific about what succeeded or failed

OUTPUT FORMAT (exactly):
VERDICT: PASS or FAIL
REASON: One clear sentence explaining why
CONFIDENCE: A number between 0.0 and 1.0"""

    scores: list[Score] = []
    for attempt in range(retries):
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude",
                "-p",
                prompt,
                "--model",
                JUDGE_MODEL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            response = stdout.decode().strip()
            score = parse_score(response)
            scores.append(score)

            if score.confidence >= JUDGE_LOW_CONFIDENCE_THRESHOLD:
                return score

        except Exception as e:
            scores.append(
                Score(
                    passed=False,
                    reasons=[f"Judge error (attempt {attempt + 1}): {e}"],
                    confidence=0.0,
                )
            )

    return (
        _consensus_score(scores)
        if scores
        else Score(passed=False, reasons=["Judge failed all retries"], confidence=0.0)
    )


def _consensus_score(scores: list[Score]) -> Score:
    """Return consensus from multiple judge attempts."""
    if not scores:
        return Score(passed=False, reasons=["No scores"], confidence=0.0)

    pass_count = sum(1 for s in scores if s.passed)
    fail_count = len(scores) - pass_count

    passed = pass_count > fail_count
    avg_confidence = sum(s.confidence for s in scores) / len(scores)
    all_reasons = [r for s in scores for r in s.reasons]

    return Score(
        passed=passed,
        reasons=[
            f"Consensus ({pass_count}/{len(scores)} pass): {all_reasons[0] if all_reasons else 'No reason'}"
        ],
        confidence=avg_confidence,
    )


def parse_score(response: str) -> Score:
    """Parse judge response into Score."""
    clean = response.strip()
    lines = clean.split("\n")

    passed = False
    reasons = []
    confidence = 0.5

    for line in lines:
        line_upper = line.upper().strip()

        if line_upper.startswith("VERDICT:"):
            verdict_part = line_upper.replace("VERDICT:", "").strip()
            passed = verdict_part.startswith("PASS")

        elif line_upper.startswith("REASON:"):
            reason = line.split(":", 1)[1].strip() if ":" in line else ""
            if reason:
                reasons.append(reason)

        elif line_upper.startswith("CONFIDENCE:"):
            conf_part = line.split(":", 1)[1].strip() if ":" in line else ""
            conf_match = re.search(r"(\d+\.?\d*)", conf_part)
            if conf_match:
                try:
                    conf = float(conf_match.group(1))
                    if 0 <= conf <= 1:
                        confidence = conf
                except ValueError:
                    pass

    if not reasons:
        upper = clean.upper()
        if "PASS" in upper or "FAIL" in upper:
            passed = (
                "PASS" in upper and upper.index("PASS") < upper.index("FAIL")
                if "FAIL" in upper
                else "PASS" in upper
            )
            reasons.append(clean[:200])

    return Score(
        passed=passed,
        reasons=reasons,
        confidence=confidence,
    )
