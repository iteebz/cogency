"""Tool formatting for LLM consumption."""

import json


def format_tools(tools_json: str, truncate: bool = True) -> str:
    """Format tool executions as natural language for LLM consumption."""
    if not tools_json:
        return ""

    try:
        tool_executions = json.loads(tools_json)
    except (json.JSONDecodeError, TypeError):
        # Fallback for malformed JSON
        return tools_json[:200] + "..." if truncate and len(tools_json) > 200 else tools_json

    if not tool_executions:
        return ""

    formatted_pairs = []
    for execution in tool_executions:
        call = execution.get("call", {})
        result = execution.get("result", "")

        # Format call
        name = call.get("name", "unknown")
        args = call.get("args", {})

        if args:
            # Truncate long argument values for readability
            truncated_args = {}
            for k, v in args.items():
                if truncate and hasattr(v, "__len__") and len(v) > 50:
                    truncated_args[k] = f"{str(v)[:47]}..."
                else:
                    truncated_args[k] = v
            arg_str = ", ".join(f"{k}={repr(v)}" for k, v in truncated_args.items())
            call_str = f"{name}({arg_str})"
        else:
            call_str = f"{name}()"

        # Natural language format - same as old working version
        if truncate and hasattr(result, "__len__") and len(str(result)) > 100:
            result_str = f"{str(result)[:97]}..."
        else:
            result_str = str(result)

        formatted_pairs.append(f"Tool {call_str}: {result_str}")

    return "\n".join(formatted_pairs)
