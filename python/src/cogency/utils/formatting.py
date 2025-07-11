import json
from typing import Any, Callable, Dict


def _format_plan(reasoning: str, _: Dict[str, Any]) -> str:
    try:
        plan_data = json.loads(reasoning)
        intent_text = plan_data.get("intent")
        reasoning_text = plan_data.get(
            "reasoning", f"No reasoning provided in plan: {reasoning}"
        )
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
    return f"{tool_used} -> {tool_result}"


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
    lines = [f"--- Execution Trace (ID: {trace.get('trace_id', 'N/A')}) ---"]

    for step in trace.get("steps", []):
        node = step.get("node", "unknown").upper()
        output_data = step.get("output_data", {})
        reasoning = step.get("reasoning", "")

        formatter = NODE_FORMATTERS.get(node, _format_default)
        summary = formatter(reasoning, output_data)

        lines.append(f"{node:<8} | {summary}")

    lines.append("--- End Trace ---")
    return "\n".join(lines)
