"""Consolidated parsing utilities - clean extraction from LLM responses."""

import json
import re
from typing import Any, Callable, Dict, List, Optional

from resilient_result import Result


def normalize_reasoning(val: Any) -> List[str]:
    """Normalizes the 'reasoning' field into a list of strings."""
    if isinstance(val, str):
        return [val]
    elif isinstance(val, dict):
        # Assuming a common case where dict might have a 'thought' or 'message' key
        if "thought" in val:
            return [val["thought"]]
        elif "message" in val:
            return [val["message"]]
        return [str(val)]  # Fallback for unexpected dict structure
    elif isinstance(val, list):
        # Flatten list, ensuring all elements are strings
        normalized_list = []
        for item in val:
            if isinstance(item, str):
                normalized_list.append(item)
            elif isinstance(item, dict):
                if "thought" in item:
                    normalized_list.append(item["thought"])
                elif "message" in item:
                    normalized_list.append(item["message"])
                else:
                    normalized_list.append(str(item))
            else:
                normalized_list.append(str(item))
        return normalized_list
    return [str(val)]  # Catch-all for any other unexpected type


def parse_json(response: str, trace_fn: Optional[Callable[[str], None]] = None) -> Result:
    """Extract JSON from LLM response - clean Result pattern.

    Handles:
    - Markdown code fences (```json and ```)
    - Proper brace matching for JSON objects
    - Regex-based pattern extraction for common failure modes
    - Graceful Result.fail() on errors

    Args:
        response: Raw LLM response string

    Returns:
        Result.ok(data) or Result.fail(error)
    """
    if not response or not isinstance(response, str):
        return Result.fail("Empty or invalid response")

    # Try direct JSON parsing first (fastest path)
    try:
        data = json.loads(response.strip())
        return Result.ok(data)
    except json.JSONDecodeError:
        pass

    # Clean and extract JSON text from markdown
    json_text = _clean_json(response.strip())
    if not json_text:
        return Result.fail("No JSON content found")

    try:
        data = json.loads(json_text)
        return Result.ok(data)
    except json.JSONDecodeError as e:
        # Fallback 1: Use incremental parser to recover partial JSON
        try:
            for obj in _extract_json_stream(response):
                if trace_fn:
                    trace_fn(
                        "JSON recovery: extracted first valid object from multi-object response"
                    )
                return Result.ok(obj)  # Return first valid JSON object
        except Exception:
            pass

        # Fallback 2: Regex-based pattern extraction for common failure modes
        try:
            extracted_json = _extract_with_patterns(response)
            if extracted_json:
                if trace_fn:
                    trace_fn(
                        f"JSON recovery: extracted using regex patterns - {extracted_json[:100]}..."
                    )
                data = json.loads(extracted_json)
                return Result.ok(data)
        except (json.JSONDecodeError, Exception):
            pass

        # All fallbacks failed - this is where self-correction would trigger
        if trace_fn:
            trace_fn(f"JSON parsing failed after all fallbacks: {str(e)}")

        return Result.fail(f"JSON decode error: {str(e)}")


def _clean_json(response: str) -> str:
    """Extract JSON from markdown code blocks with brace matching."""
    # Use a more flexible regex to find JSON content
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
    if json_match:
        response = json_match.group(1).strip()

    # Extract JSON object with proper brace matching
    return _extract_json(response)


def _extract_json(text: str) -> str:
    """Extract JSON object with proper brace matching, accounting for strings."""
    start_idx = text.find("{")
    if start_idx == -1:
        return text

    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start_idx:], start_idx):
        if escape_next:
            escape_next = False
            continue

        if char == "\\" and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx : i + 1]

    return text


def _extract_json_stream(text: str):
    """Extract JSON objects incrementally - returns FIRST valid object only.

    This handles cases where LLMs generate multiple JSON objects despite
    explicit instructions to output only one per iteration.
    """
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(text):
        # Skip whitespace and non-JSON characters
        while pos < len(text) and text[pos] not in "{[":
            pos += 1

        if pos >= len(text):
            break

        try:
            obj, index = decoder.raw_decode(text[pos:])
            yield obj  # Return first valid JSON object found
            return  # Stop after first valid object - don't process subsequent ones
        except json.JSONDecodeError:
            pos += 1


def _extract_with_patterns(text: str) -> Optional[str]:
    """Extract JSON using regex patterns for common LLM failure modes."""
    patterns = [
        # Pattern 1: JSON surrounded by explanation text
        r'(?:```json\s*)?(\{[^{}]*"thinking"[^{}]*"tool_calls"[^{}]*\})',
        # Pattern 2: JSON with trailing text after closing brace
        r'(\{[^{}]*"thinking"[^{}]*"tool_calls"[^{}]*\})[^{}]*$',
        # Pattern 3: JSON with leading explanation
        r'(?:Here\'s|Here is|The response is).*?(\{[^{}]*"thinking"[^{}]*"tool_calls"[^{}]*\})',
        # Pattern 4: Basic JSON structure recovery
        r'(\{[^{}]*(?:"thinking"|"tool_calls"|"reflect"|"plan")[^{}]*\})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Validate extracted candidate has required structure
            if '"thinking"' in candidate or '"tool_calls"' in candidate:
                return candidate

    return None


def parse_tool_calls(json_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Extract tool calls from parsed JSON. Return None if no tool calls."""
    if not json_data:
        return None

    # Direct tool_calls array - clean format only
    tool_calls = json_data.get("tool_calls")

    if tool_calls is None:
        return None

    # Limit tool calls to prevent JSON parsing issues
    from cogency.config import MAX_TOOL_CALLS

    if len(tool_calls) > MAX_TOOL_CALLS:
        # Truncate to max allowed tool calls
        return tool_calls[:MAX_TOOL_CALLS]

    return tool_calls


def recover_json(response: str) -> Result:
    """Extract JSON from broken LLM responses - Result pattern."""
    if not response:
        return Result.fail("No response to recover")

    return parse_json(response)


async def parse_json_with_correction(
    response: str,
    llm_fn: Optional[Callable] = None,
    trace_fn: Optional[Callable[[str], None]] = None,
    max_attempts: int = 2,
) -> Result:
    """Parse JSON with self-correction loop for malformed responses."""

    # Try normal parsing first
    result = parse_json(response, trace_fn)
    if result.success or not llm_fn:
        return result

    # Attempt self-correction
    for attempt in range(max_attempts):
        if trace_fn:
            trace_fn(f"JSON self-correction attempt {attempt + 1}/{max_attempts}")

        correction_prompt = self_correct_json(response, result.error)

        try:
            corrected_response = await llm_fn([{"role": "user", "content": correction_prompt}])
            corrected_result = parse_json(corrected_response, trace_fn)

            if corrected_result.success:
                if trace_fn:
                    trace_fn(f"JSON self-correction succeeded on attempt {attempt + 1}")
                return corrected_result
            else:
                response = corrected_response  # Try again with corrected response

        except Exception as e:
            if trace_fn:
                trace_fn(f"JSON self-correction failed: {str(e)}")
            break

    # Self-correction failed, return original error
    if trace_fn:
        trace_fn("JSON self-correction exhausted all attempts, falling back to error")
    return result


def self_correct_json(malformed_response: str, error_msg: str) -> str:
    """Generate self-correction prompt for malformed JSON responses."""
    return f"""The previous response contained malformed JSON. Please fix it and return only valid JSON.

Error: {error_msg}

Malformed response:
{malformed_response}

CRITICAL: Return ONLY a single valid JSON object with this exact structure:
{{
  "thinking": "your reasoning here",
  "tool_calls": [array of tool calls or empty array],
  "switch_to": null,
  "switch_why": null
}}"""


def fallback_prompt(reason: str, system: str = None, schema: str = None) -> str:
    """Build fallback prompt when reasoning fails."""
    if schema:
        prompt = f"Reasoning failed: {reason}. Generate valid JSON matching schema: {schema}"
    else:
        prompt = f"Reasoning failed: {reason}. Provide helpful response based on context."

    return f"{system}\n\n{prompt}" if system else prompt


def fallback_response(error: Exception, schema: str = None) -> str:
    """Format error as JSON or text."""
    if schema:
        msg = str(error).replace('"', '\\"')
        return f'{{"error": "Technical issue", "details": "{msg}"}}'
    return f"Technical issue: {error}. Let me help based on our conversation."
