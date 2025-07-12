import json
from typing import Any, Callable, Dict


def _format_plan(reasoning: str, _: Dict[str, Any]) -> str:
    try:
        plan_data = json.loads(reasoning)
        intent_text = plan_data.get("intent")
        reasoning_text = plan_data.get("reasoning", "Planning decision made")
        strategy_text = plan_data.get("strategy")
        action = plan_data.get("action")

        # Format based on action type
        if action == "tool_needed":
            return f"Tool needed: {reasoning_text}"
        elif action == "direct_response":
            return f"Direct response: {reasoning_text}"
        else:
            formatted_output = []
            if intent_text:
                formatted_output.append(f"Intent: {intent_text}")
            formatted_output.append(reasoning_text)  # Remove "Reasoning:" prefix
            if strategy_text:
                formatted_output.append(f"Strategy: {strategy_text}")
            return " - ".join(formatted_output)
    except json.JSONDecodeError:
        # Handle common pattern where LLM outputs "Reasoning: ..." instead of JSON
        if reasoning.startswith("Reasoning: "):
            return reasoning[11:]  # Remove "Reasoning: " prefix
        return reasoning


def _format_reason(reasoning: str, _: Dict[str, Any]) -> str:
    return reasoning.replace("LLM Output: ", "")


def _format_act(_: str, output_data: Dict[str, Any]) -> str:
    tool_used = output_data.get("tool_used", "N/A")
    output_data.get("tool_result", "N/A")

    # Simple, clean execution message
    if tool_used == "calculator":
        return "Executing calculation..."
    elif tool_used == "web_search":
        return "Searching the web..."
    elif tool_used == "file_manager":
        return "Performing file operation..."
    else:
        return f"Executing {tool_used}..."


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

    for step in steps:
        node = step.get("node", "unknown").upper()
        output_data = step.get("output_data", {})
        reasoning = step.get("reasoning", "")

        formatter = NODE_FORMATTERS.get(node, _format_default)
        summary = formatter(reasoning, output_data)

        # Use cleaner step labels without timing
        node_label = f"[{node}]"
        lines.append(f"{node_label:<10} {summary}")

    return "\n".join(lines)
