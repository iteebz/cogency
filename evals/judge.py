"""Judge protocol - LLM-based test evaluation."""

from dataclasses import dataclass


@dataclass
class Judgment:
    passed: bool
    reason: str


async def judge(result: dict, judge_llm) -> Judgment:
    """Judge test result using LLM."""
    if result.get("error"):
        return Judgment(passed=False, reason=f"Test error: {result['error']}")

    if not judge_llm:
        return Judgment(passed=False, reason="No judge configured")

    stream_text = "\n".join(result.get("stream", []))

    prompt = f"""Evaluate this test result:

CRITERIA: {result["criteria"]}
PROMPT: {result["prompt"]}
AGENT_STREAM:
{stream_text}

Did the agent meet the criteria? Answer PASS or FAIL with brief reason.

Format: PASS: reason | FAIL: reason"""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = await judge_llm.generate(messages)

        clean = response.strip().upper()
        if clean.startswith("PASS"):
            return Judgment(passed=True, reason=response.strip())
        if clean.startswith("FAIL"):
            return Judgment(passed=False, reason=response.strip())
        return Judgment(passed=False, reason=f"Invalid response: {response}")

    except Exception as e:
        return Judgment(passed=False, reason=f"Judge error: {str(e)}")
