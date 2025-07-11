import json
from typing import Any, Dict, Optional, Tuple


def parse_plan_response(response: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Parse plan node JSON response to determine routing action."""
    try:
        data = json.loads(response)
        action = data.get("action")
        if action == "tool_needed":
            return "reason", data
        elif action == "direct_response":
            return "respond", data
        else:
            # Fallback to prefix parsing for compatibility
            if response.startswith("TOOL_NEEDED:"):
                return "reason", {"action": "tool_needed", "content": response[12:]}
            return "respond", {"action": "direct_response", "content": response}
    except json.JSONDecodeError:
        # Fallback to prefix parsing
        if response.startswith("TOOL_NEEDED:"):
            return "reason", {"action": "tool_needed", "content": response[12:]}
        return "respond", {"action": "direct_response", "content": response}


def parse_reflect_response(response: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Parse reflect node JSON response to determine routing action."""
    try:
        data = json.loads(response)
        status = data.get("status")
        if status == "continue":
            return "reason", data
        elif status == "complete":
            return "respond", data
        else:
            # Fallback to prefix parsing for compatibility
            if response.startswith("TASK_COMPLETE:"):
                return "respond", {"status": "complete", "content": response[14:]}
            return "reason", {"status": "continue", "content": response}
    except json.JSONDecodeError:
        # Fallback to prefix parsing
        if response.startswith("TASK_COMPLETE:"):
            return "respond", {"status": "complete", "content": response[14:]}
        return "reason", {"status": "continue", "content": response}


def extract_tool_call(llm_response: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Extract tool call from LLM response."""
    if llm_response.startswith("TOOL_CALL:"):
        try:
            tool_call_str = llm_response[len("TOOL_CALL:") :].strip()

            import re

            match = re.match(r"(\w+)\((.*)\)", tool_call_str)
            if match:
                tool_name = match.group(1)
                args_str = match.group(2)
                return tool_name, {"raw_args": args_str}
        except Exception:
            pass

    return None
