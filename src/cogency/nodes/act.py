"""Act node - pure tool execution."""
import time
from typing import List, Optional, Dict, Any

from cogency.tools.base import BaseTool
from cogency.types import AgentState
from cogency.tracing import trace_node
from cogency.tools.executor import parse_tool_call, execute_single_tool, execute_parallel_tools
from cogency.tools.result import extract_tool_data, is_tool_success, get_tool_error
from cogency.types import ToolCall, MultiToolCall
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
    
    tool_call = parse_tool_call(tool_call_str)
    execution_results = {}
    
    # Stream ACT message with actual tool calls - SINGLE MESSAGE
    if streaming_callback:
        if isinstance(tool_call, MultiToolCall):
            tool_names = [call.name for call in tool_call.calls]
            await AgentMessenger.act(streaming_callback, tool_names)
        elif isinstance(tool_call, ToolCall):
            await AgentMessenger.act(streaming_callback, [tool_call.name])
        else:
            await AgentMessenger.act(streaming_callback, [])
    
    # Execute tools and add results to context (this is the OBSERVE step)
    if isinstance(tool_call, MultiToolCall):
        # Convert ToolCall objects to (name, args) tuples for parallel execution
        tool_tuples = [(call.name, call.args) for call in tool_call.calls]
        execution_results = await execute_parallel_tools(tool_tuples, selected_tools, context)
    elif isinstance(tool_call, ToolCall):
        tool_name, parsed_args, tool_output = await execute_single_tool(
            tool_call.name, tool_call.args, selected_tools, context
        )
        
        if not is_tool_success(tool_output):
            # Add error to context so agent can reason about it
            error_msg = get_tool_error(tool_output) or f"Tool {tool_name} failed"
            context.add_message("system", f"Tool {tool_name} failed: {error_msg}")
            execution_results = {"success": False, "errors": [error_msg]}
        else:
            # Tool executed successfully
            tool_data = extract_tool_data(tool_output)
            if tool_data is None:
                context.add_message("system", f"Tool {tool_name} executed but returned no data")
                execution_results = {"success": False, "errors": [f"Tool {tool_name} returned no data"]}
            else:
                context.add_message("system", f"Tool {tool_name} result: {tool_data}")
                context.add_tool_result(tool_name, parsed_args, tool_data)
                execution_results = {"success": True, "results": [tool_data]}
    
    execution_time = time.time() - start_time
    
    # Stream OBSERVE message with actual results - HUMAN READABLE ONLY
    if streaming_callback:
        if execution_results.get("success"):
            results = execution_results.get("results", [])
            if results:
                # Create human-readable summary of results
                if len(results) == 1:
                    # Single result - show meaningful summary
                    result = results[0]
                    if isinstance(result, dict):
                        # Extract key information for display
                        if "temperature" in result:  # Weather
                            await AgentMessenger.observe(streaming_callback, f"Weather: {result.get('temperature', 'N/A')}, {result.get('condition', 'N/A')}")
                        elif "datetime" in result:  # Timezone
                            await AgentMessenger.observe(streaming_callback, f"Time: {result.get('datetime', 'N/A')}")
                        else:
                            await AgentMessenger.observe(streaming_callback, f"Result: {str(result)[:50]}...")
                    else:
                        # Simple result (like calculator)
                        await AgentMessenger.observe(streaming_callback, str(result))
                else:
                    # Multiple results
                    await AgentMessenger.observe(streaming_callback, f"Got {len(results)} results")
            else:
                await AgentMessenger.observe(streaming_callback, "Tool executed successfully")
        else:
            errors = execution_results.get("errors", ["Tool execution failed"])
            error_summary = errors[0] if errors else "Tool execution failed"
            await AgentMessenger.observe(streaming_callback, error_summary)
        
        # Add spacing before next reasoning cycle
        await AgentMessenger.spacing(streaming_callback)
    
    # Store execution results in state with consistent format
    state["execution_results"] = execution_results
    
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