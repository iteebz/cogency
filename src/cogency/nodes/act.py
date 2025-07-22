"""Act node - pure tool execution."""

import time
from typing import Dict, List, Optional

from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.executor import parse_tool_calls, run_tools


async def act(state: State, *, tools: List[BaseTool], config: Optional[Dict] = None) -> State:
    """Act: execute tools based on reasoning decision."""
    time.time()

    tool_call_str = state.get("tool_calls")
    if not tool_call_str:
        return {"execution_results": {"type": "no_action"}, "next_node": "reason"}

    context = state.context
    selected_tools = state.get("selected_tools", tools)

    tool_calls = parse_tool_calls(tool_call_str)
    if not tool_calls:
        await state.output.send("trace", "No valid tool calls parsed", node="act")
        return {"execution_results": {"type": "no_action"}, "next_node": "reason"}

    # Clear cognitive state indicator for execution
    tool_names = [c['name'] for c in tool_calls]
    
    tool_tuples = [(call["name"], call["args"]) for call in tool_calls]
    
    # Show detailed tool calls with actual parameters
    for call in tool_calls:
        tool_name = call["name"]
        args = call["args"]
        # Format args nicely - truncate long values
        formatted_args = {}
        for k, v in args.items():
            if isinstance(v, str) and len(v) > 100:
                formatted_args[k] = f"{v[:100]}..."
            else:
                formatted_args[k] = v
        await state.output.send(
            "trace", f"{tool_name}({formatted_args})", node="act"
        )
    
    await state.output.send(
        "trace", f"Executing {len(tool_calls)} tools: {tool_names}", node="act"
    )
    execution_results = await run_tools(tool_tuples, selected_tools, context)

    # Simple result display - just show what happened
    successes = execution_results.get("results", [])
    errors = execution_results.get("errors", [])
    
    for success in successes:
        await state.output.send(
            "tool_execution_summary", success.get('result', 'success'), tool_name=success['tool_name'], success=True, status="success"
        )
    
    for error in errors:
        await state.output.send(
            "tool_execution_summary", error.get('error', 'failed'), tool_name=error['tool_name'], success=False, status="failed"
        )

    success_count = execution_results.get("successful_count", 0)
    total_count = len(tool_calls)
    # This message is still a trace, as it's about the internal process of tool completion
    await state.output.send(
        "trace", f"Tools completed: {success_count}/{total_count} successful", node="act", status="success" if success_count == total_count else "failed", output=execution_results
    )

    # Update flow state
    state["execution_results"] = execution_results
    state["next_node"] = "reason"

    return state
