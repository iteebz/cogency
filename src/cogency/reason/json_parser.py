"""Canonical JSON parsing for LLM responses - consolidated robust implementation."""

import json
from typing import Any, Optional

from cogency.events import emit

from .parsing import _parse_json


async def parse_reasoning_json(response: str, llm, iteration: int = 1) -> dict[str, Any]:
    """Parse LLM response to reasoning JSON - canonical approach with robust fallbacks.

    Args:
        response: Raw LLM response text
        llm: LLM provider for self-correction
        iteration: Current reasoning iteration

    Returns:
        Parsed reasoning dict with standard fields
    """
    # Use robust parsing with fallback recovery
    parse_result = _parse_json(response)

    if parse_result.is_ok():
        parsed = parse_result.unwrap()
        return _build_reasoning_response(parsed, iteration)

    # Try self-correction via LLM
    emit("reason", state="json_error", raw_response=response[:200])

    corrected = await _self_correct_json(response, llm)
    if corrected is not None:
        return _build_reasoning_response(corrected, iteration)

    # Fallback to natural language response
    emit("reason", state="json_correction_failed")
    return {
        "assessment": "JSON formatting failed, using natural language response",
        "approach": "Direct response",
        "response": response.strip(),
        "actions": [],
    }


async def _self_correct_json(response: str, llm) -> Optional[dict[str, Any]]:
    """Ask LLM to self-correct malformed JSON."""
    correction_prompt = f"""You provided this response but it wasn't valid JSON:
{response}

Please provide the same reasoning as a valid JSON object with this exact structure:
{{
  "secure": true,
  "assessment": "what you understand about this query",
  "approach": "how you plan to handle this",
  "response": "your response here or null if actions needed",
  "actions": [list of actions if any]
}}

RESPOND WITH ONLY THE JSON OBJECT:"""

    try:
        correction_messages = [
            {
                "role": "system",
                "content": "Convert the previous response to valid JSON format.",
            },
            {"role": "user", "content": correction_prompt},
        ]

        correction_result = await llm.generate(correction_messages)
        correction_data = correction_result.unwrap()
        correction_text = correction_data["content"]

        corrected_json = json.loads(correction_text.strip())

        emit(
            "reason",
            state="json_corrected",
            original_length=len(response),
            corrected_length=len(correction_text),
        )

        return corrected_json

    except Exception:
        return None


def _build_reasoning_response(parsed: dict[str, Any], iteration: int) -> dict[str, Any]:
    """Build canonical reasoning response from parsed JSON."""
    # Check security assessment for first iteration
    if iteration == 1 and parsed.get("secure") is False:
        emit("reason", state="security_violation", iteration=iteration)
        return {
            "reasoning": parsed.get("reasoning", "Security assessment failed"),
            "response": parsed.get("response", "I cannot assist with that request."),
            "actions": [],
        }

    # Standard reasoning response
    return {
        "assessment": parsed.get("assessment", "No assessment provided"),
        "approach": parsed.get("approach", "No approach specified"),
        "response": parsed.get("response"),
        "actions": parsed.get("actions", []),
    }
