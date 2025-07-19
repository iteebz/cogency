"""Act node - pure tool execution."""
import time
from typing import List, Optional, Dict, Any

from cogency.tools.base import BaseTool
from cogency.common.types import AgentState
from cogency.utils.tracing import trace_node
from cogency.execution.executor import parse_tool_call, execute_single_tool, execute_parallel_tools
from cogency.common.schemas import ToolCall, MultiToolCall
from cogency.streaming.messaging import AgentMessenger


@trace_node("act")
async def act_node(state: AgentState, *, tools: List[BaseTool], config: Optional[Dict] = None) -> AgentState:
    """Act: execute tools based on reasoning decision."""
    start_time = time.time()
    
    # Get streaming callback if available
    streaming_callback = None
    if config and "configurable" in config:
        streaming_callback = config["configurable"].get("streaming_callback")
    
    # Get tool calls from reasoning
    tool_call_str = state.get("tool_calls")
    if not tool_call_str:
        state["execution_results"] = {"type": "no_action", "time": time.time() - start_time}
        state["next_node"] = "reason"  # Always return to reason for reflection
        return state
    
    context = state["context"]
    selected_tools = state.get("selected_tools", tools)
    
    tool_call = parse_tool_call(tool_call_str)
    execution_results = {}
    
    # Stream ACT message with actual tool calls
    if streaming_callback:
        if isinstance(tool_call, MultiToolCall):
            for call in tool_call.calls:
                args_str = ", ".join([f"{k}={repr(v)}" for k, v in call.args.items()]) if call.args else ""
                await AgentMessenger.act(streaming_callback, [f"{call.name}({args_str})"])
        elif isinstance(tool_call, ToolCall):
            args_str = ", ".join([f"{k}={repr(v)}" for k, v in tool_call.args.items()]) if tool_call.args else ""
            await AgentMessenger.act(streaming_callback, [f"{tool_call.name}({args_str})"])
        else:
            await AgentMessenger.act(streaming_callback, [])
    
    # Execute tools and add results to context (this is the OBSERVE step)
    if isinstance(tool_call, MultiToolCall):
        execution_results = await execute_parallel_tools(tool_call.calls, selected_tools, context)
    elif isinstance(tool_call, ToolCall):
        tool_name, parsed_args, tool_output = await execute_single_tool(
            tool_call.name, tool_call.args, selected_tools, context
        )
        
        if isinstance(tool_output, dict) and tool_output.get("success") is False:
            # Add error to context so agent can reason about it
            error_msg = f"Tool {tool_name} failed: {tool_output.get('error')}"
            context.add_message("system", error_msg)
            execution_results = {"success": False, "errors": [error_msg]}
        else:
            # Add successful result to context
            result = tool_output.get("result") if isinstance(tool_output, dict) else tool_output
            context.add_message("system", f"Tool {tool_name} result: {result}")
            context.add_tool_result(tool_name, parsed_args, result)
            execution_results = {"success": True, "results": [result]}
    
    execution_time = time.time() - start_time
    
    # Stream OBSERVE message with actual results
    if streaming_callback:
        if execution_results.get("success"):
            results = execution_results.get("results", [])
            if results:
                # Show first result as summary, truncate if too long
                result_summary = str(results[0])
                if len(result_summary) > 100:
                    result_summary = result_summary[:97] + "..."
                await AgentMessenger.observe(streaming_callback, result_summary)
            else:
                await AgentMessenger.observe(streaming_callback, "Tool executed successfully")
        else:
            errors = execution_results.get("errors", ["Tool execution failed"])
            error_summary = errors[0] if errors else "Tool execution failed"
            if len(error_summary) > 100:
                error_summary = error_summary[:97] + "..."
            await AgentMessenger.observe(streaming_callback, error_summary)
    
    # Store execution results in state
    state["execution_results"] = {
        "type": "tool_execution",
        "results": execution_results,
        "time": execution_time
    }
    
    # Update adaptive reasoning controller metrics if available
    controller = state.get("adaptive_controller")
    if controller:
        # Convert execution results to format expected by controller
        controller_metrics = {
            "total_executed": 1 if isinstance(tool_call, ToolCall) else len(tool_call.calls) if isinstance(tool_call, MultiToolCall) else 0,
            "successful_count": 1 if execution_results.get("success") else 0,
            "failed_count": 0 if execution_results.get("success") else 1
        }
        controller.update_iteration_metrics(controller_metrics, execution_time)
    
    # Always route back to reason for reflection on results
    state["next_node"] = "reason"
    
    return state