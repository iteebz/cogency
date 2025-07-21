"""Act node - pure tool execution."""
import time
from typing import List, Optional, Dict, Any

from cogency.tools.base import BaseTool
from cogency.state import State
from cogency.tools.executor import parse_tool_calls, run_tools

async def act(state: State, *, tools: List[BaseTool], config: Optional[Dict] = None) -> State:
    """Act: execute tools based on reasoning decision."""
    start_time = time.time()
    
    tool_call_str = state.get("tool_calls")
    if not tool_call_str:
        return {"execution_results": {"type": "no_action"}, "next_node": "reason"}
    
    context = state.context
    selected_tools = state.get("selected_tools", tools)
    
    tool_calls = parse_tool_calls(tool_call_str)
    if not tool_calls:
        await state.output.send("trace", "No valid tool calls parsed", node="act")
        return {"execution_results": {"type": "no_action"}, "next_node": "reason"}
    
    tool_tuples = [(call["name"], call["args"]) for call in tool_calls]
    await state.output.send("trace", f"Executing {len(tool_calls)} tools: {[c['name'] for c in tool_calls]}", node="act")
    execution_results = await run_tools(tool_tuples, selected_tools, context)
    
    # Stream results via Output
    for call, result in zip(tool_calls, execution_results.get("results", [])):
        await state.output.send(
            "tool_execution",
            content="", # content is not used in this message type
            tool_name=call["name"],
            params=call["args"],
            result=result.get("result"),
            success=result.get("success", False)
        )

    success_count = execution_results.get("successful_count", 0)
    total_count = len(tool_calls)
    await state.output.send("trace", f"Tools completed: {success_count}/{total_count} successful", node="act")

    # Update flow state
    state["execution_results"] = execution_results
    state["next_node"] = "reason"
    
    return state