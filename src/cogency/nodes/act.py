"""Act node - pure tool execution."""
import time
from typing import List, Optional, Dict, Any

from cogency.tools.base import BaseTool
from cogency.types import AgentState
from cogency.tracing import trace_node
from cogency.tools.executor import parse_tool_calls, execute_single_tool, execute_parallel_tools
from cogency.tools.result import extract_tool_data, is_tool_success, get_tool_error
# Eliminated import ceremony - using simple strings
from cogency.types import ToolCall
from cogency.messaging import AgentMessenger


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
    
    tool_calls = parse_tool_calls(tool_call_str)
    if not tool_calls:
        state["execution_results"] = {"type": "no_action", "time": time.time() - start_time}
        state["next_node"] = "reason"
        return state
    
    # No more ceremony - tool execution will show the actual calls
    
    # Execute tools - always use parallel execution for consistency
    tool_tuples = [(call.name, call.args) for call in tool_calls]
    execution_results = await execute_parallel_tools(tool_tuples, selected_tools, context)
    
    execution_time = time.time() - start_time
    
    # Stream tool execution with new clean format
    if streaming_callback:
        if execution_results.get("success"):
            results = execution_results.get("results", [])
            if results and len(tool_calls) == len(results):
                # Show each tool execution with result
                for i, (call, result) in enumerate(zip(tool_calls, results)):
                    # Extract actual result data
                    result_data = result.get("result") if isinstance(result, dict) and "result" in result else result
                    await AgentMessenger.tool_execution(
                        streaming_callback, 
                        call.name, 
                        call.args or {}, 
                        result_data, 
                        success=True
                    )
            else:
                # Fallback for mismatched results
                for call in tool_calls:
                    await AgentMessenger.tool_execution(
                        streaming_callback, 
                        call.name, 
                        call.args or {}, 
                        "completed", 
                        success=True
                    )
        else:
            # Show failed executions
            errors = execution_results.get("errors", [])
            for i, call in enumerate(tool_calls):
                error_msg = errors[i] if i < len(errors) else "execution failed"
                await AgentMessenger.tool_execution(
                    streaming_callback, 
                    call.name, 
                    call.args or {}, 
                    error_msg, 
                    success=False
                )
        
        # No spacing - keep it dense and scannable
    
    # Store execution results in state with consistent format
    state["execution_results"] = execution_results
    
    # Update adaptive reasoning controller metrics if available
    controller = state.get("adaptive_controller")
    if controller:
        controller_metrics = {
            "total_executed": len(tool_calls),
            "successful_count": execution_results.get("successful_count", 0),
            "failed_count": execution_results.get("failed_count", 0)
        }
        controller.update_iteration_metrics(controller_metrics, execution_time)
    
    # Always route back to reason for reflection on results
    state["next_node"] = "reason"
    
    return state