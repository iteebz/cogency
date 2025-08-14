"""Natural language response parsing."""

import re


def parse(response: str) -> dict:
    """Parse natural language response for tool calls and final answers."""

    # Check for completion
    if "final answer" in response.lower():
        return {"action": {"type": "final_answer"}, "final_answer": response}

    # Look for USE: tool_name(args)
    match = re.search(r"USE:\s*(\w+)\((.*?)\)", response, re.IGNORECASE)
    if match:
        tool_name = match.group(1)
        args_str = match.group(2).strip()

        args = {}
        if args_str:
            # Handle simple patterns: arg="value" or arg1="value1", arg2="value2"
            for part in args_str.split(","):
                if "=" in part:
                    key, value = part.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    args[key] = value

        return {"action": {"type": "tool_call", "name": tool_name, "args": args}}

    # Continue reasoning
    return {"action": {"type": "continue"}}
