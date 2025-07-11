import json
from typing import Any, Callable, Dict


def _format_plan(reasoning: str, _: Dict[str, Any]) -> str:
    try:
        plan_data = json.loads(reasoning)
        intent_text = plan_data.get("intent")
        reasoning_text = plan_data.get("reasoning", f"No reasoning provided in plan: {reasoning}")
        strategy_text = plan_data.get("strategy")

        formatted_output = []
        if intent_text:
            formatted_output.append(f"Intent: {intent_text}")
        formatted_output.append(f"Reasoning: {reasoning_text}")
        if strategy_text:
            formatted_output.append(f"Strategy: {strategy_text}")

        return " - ".join(formatted_output)
    except json.JSONDecodeError:
        return f"LLM returned non-JSON plan: {reasoning}"


def _format_reason(reasoning: str, _: Dict[str, Any]) -> str:
    return reasoning.replace("LLM Output: ", "")


def _format_act(_: str, output_data: Dict[str, Any]) -> str:
    tool_used = output_data.get("tool_used", "N/A")
    tool_result = output_data.get("tool_result", "N/A")
    tool_input = output_data.get("tool_input", {})

    # Format tool call with parameters
    if tool_input:
        params = ", ".join([f"{k}={v}" for k, v in tool_input.items()])
        tool_call = f"[TOOL_CALL] {tool_used}({params})"
    else:
        tool_call = f"[TOOL_CALL] {tool_used}"

    # Special formatting for web search results
    if tool_used == "web_search" and isinstance(tool_result, dict):
        if "results" in tool_result and tool_result["results"]:
            results = tool_result["results"][:3]  # Show first 3 results
            formatted_results = []
            for result in results:
                title = result.get("title", "No title")[:50]
                if len(result.get("title", "")) > 50:
                    title += "..."
                formatted_results.append(f"• {title}")
            result_summary = "\n           ".join(formatted_results)
            return f"{tool_call} -> Found {tool_result.get('total_found', 0)} results:\n           {result_summary}"
        else:
            return f"{tool_call} -> No results found"

    # Truncate long results for cleaner display
    if isinstance(tool_result, str) and len(tool_result) > 100:
        tool_result = tool_result[:97] + "..."

    return f"{tool_call} -> {tool_result}"


def _format_reflect(reasoning: str, _: Dict[str, Any]) -> str:
    return reasoning.replace("Assessment: ", "").replace("Error Description: ", "")


def _format_respond(reasoning: str, _: Dict[str, Any]) -> str:
    return reasoning.replace("LLM Output: ", "")


def _format_default(reasoning: str, _: Dict[str, Any]) -> str:
    return reasoning


NODE_FORMATTERS: Dict[str, Callable[[str, Dict[str, Any]], str]] = {
    "PLAN": _format_plan,
    "REASON": _format_reason,
    "ACT": _format_act,
    "REFLECT": _format_reflect,
    "RESPOND": _format_respond,
}


def format_trace(trace: Dict[str, Any]) -> str:
    """Formats a detailed execution trace into a human-readable summary."""
    lines = ["--- Execution Trace ---"]

    steps = trace.get("steps", [])
    if not steps:
        return "\n".join(lines + ["No steps recorded"])

    # Calculate timing information
    start_time = None
    for i, step in enumerate(steps):
        node = step.get("node", "unknown").upper()
        output_data = step.get("output_data", {})
        reasoning = step.get("reasoning", "")
        timestamp = step.get("timestamp", "")

        formatter = NODE_FORMATTERS.get(node, _format_default)
        summary = formatter(reasoning, output_data)

        # Calculate timing
        if i == 0:
            # First step - record start time
            if timestamp:
                from datetime import datetime

                try:
                    start_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    timing_info = "@0ms"
                except:
                    timing_info = ""
            else:
                timing_info = ""
        else:
            # Subsequent steps - calculate elapsed time
            if timestamp and start_time:
                try:
                    current_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    elapsed_ms = int((current_time - start_time).total_seconds() * 1000)
                    timing_info = f"@+{elapsed_ms}ms"
                except:
                    timing_info = ""
            else:
                timing_info = ""

        # Use cleaner step labels with timing
        node_label = f"[{node}]"
        if timing_info:
            lines.append(f"{node_label:<10} {timing_info:<8} {summary}")
        else:
            lines.append(f"{node_label:<10} {summary}")

    return "\n".join(lines)
