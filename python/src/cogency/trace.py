import json
from functools import wraps
from typing import Any, Callable, Dict, TypeVar

from cogency.types import AgentState

F = TypeVar("F", bound=Callable[..., Any])


def _extract_reasoning(message: str) -> str:
    """Extracts a descriptive reasoning string from a message."""
    try:
        message_json = json.loads(message)

        # Mapping of keys to their human-readable prefixes
        REASONING_MAP = {
            "reasoning": "Reasoning",
            "strategy": "Strategy",
            "assessment": "Assessment",
            "description": "Error Description",
            "answer": "Direct Answer",
            "action": "Action",
        }

        for key, prefix in REASONING_MAP.items():
            if key in message_json:
                return f"{prefix}: {message_json[key]}"

        # Fallback for unexpected JSON structure
        return f"LLM Output (JSON): {message}"

    except (json.JSONDecodeError, KeyError):
        # If it's not a JSON or doesn't have the expected keys, return the raw message
        return f"LLM Output: {message}"


@wraps(F)
def trace_node(func: F) -> F:
    """
    Decorator to trace agent node execution with detailed, developer-friendly context.
    It captures the state before and after the node runs to provide a clear delta.
    """

    def wrapper(*args, **kwargs):
        state = args[0] if args else kwargs.get("state")
        if not state or not isinstance(state, dict) or not state.get("execution_trace"):
            return func(*args, **kwargs)

        context = state.get("context")

        # 1. Capture state BEFORE node execution
        messages_before = [msg["content"] for msg in context.messages]
        tool_results_before = list(context.tool_results)

        input_data = {
            "user_query": context.current_input,
            "messages": messages_before,
            "tool_results": tool_results_before,
        }

        # 2. Execute the node
        result = func(*args, **kwargs)

        # 3. Capture state AFTER node execution and determine the delta
        context_after = result.get("context")
        messages_after = [msg["content"] for msg in context_after.messages]
        tool_results_after = list(context_after.tool_results)

        new_messages = [msg for msg in messages_after if msg not in messages_before]

        # 4. Extract detailed reasoning from the new message(s)
        reasoning = "No new message added by this node."
        if new_messages:
            reasoning = _extract_reasoning(new_messages[-1])

        # 5. Construct detailed, human-readable output data
        output_data = {"new_messages": new_messages}

        if func.__name__ == "act" and len(tool_results_after) > len(
            tool_results_before
        ):
            last_tool_result = tool_results_after[-1]
            output_data.update(
                {
                    "tool_used": last_tool_result.get("tool_name"),
                    "tool_input": last_tool_result.get("args"),
                    "tool_result": last_tool_result.get("output"),
                }
            )
            reasoning += f" | BaseTool Result: {last_tool_result.get('output')}"

        # 6. Add the detailed step to the execution trace
        state["execution_trace"].add_step(
            func.__name__, input_data, output_data, reasoning
        )

        return result

    return wrapper
