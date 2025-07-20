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
    
    # Stream beautiful ACT message with actual tool calls and params
    if streaming_callback:
        if len(tool_calls) == 1:
            # Single tool call - same line
            call = tool_calls[0]
            if call.args:
                key_params = []
                for key, value in list(call.args.items())[:2]:  # Show first 2 params
                    if isinstance(value, str) and len(value) > 20:
                        key_params.append(f"{key}='{value[:20]}...'")
                    else:
                        key_params.append(f"{key}={value}")
                param_str = f"({', '.join(key_params)})" if key_params else ""
                display = f"{call.name}{param_str}"
            else:
                display = call.name
            await AgentMessenger.act(streaming_callback, [display])
        else:
            # Multiple tool calls - each on new line for clarity
            tool_displays = []
            for call in tool_calls:
                if call.args:
                    key_params = []
                    for key, value in list(call.args.items())[:2]:  # Show first 2 params
                        if isinstance(value, str) and len(value) > 20:
                            key_params.append(f"{key}='{value[:20]}...'")
                        else:
                            key_params.append(f"{key}={value}")
                    param_str = f"({', '.join(key_params)})" if key_params else ""
                    tool_displays.append(f"  {call.name}{param_str}")
                else:
                    tool_displays.append(f"  {call.name}")
            # Send as single message with newlines for clean multi-line display
            await AgentMessenger.act(streaming_callback, ["\n".join(tool_displays)])
    
    # Execute tools - always use parallel execution for consistency
    tool_tuples = [(call.name, call.args) for call in tool_calls]
    execution_results = await execute_parallel_tools(tool_tuples, selected_tools, context)
    
    execution_time = time.time() - start_time
    
    # Stream OBSERVE message with actual results - HUMAN READABLE ONLY
    if streaming_callback:
        if execution_results.get("success"):
            results = execution_results.get("results", [])
            if results:
                # Create human-readable summary of results
                if len(results) == 1:
                    # Single result - extract actual data
                    result_data = results[0] if not isinstance(results[0], dict) or "result" not in results[0] else results[0]["result"]
                    if isinstance(result_data, dict):
                        # Extract key information for display
                        if "temperature" in result_data:  # Weather
                            await AgentMessenger.observe(streaming_callback, f"Weather: {result_data.get('temperature', 'N/A')}, {result_data.get('condition', 'N/A')}")
                        elif "datetime" in result_data:  # Timezone
                            await AgentMessenger.observe(streaming_callback, f"Time: {result_data.get('datetime', 'N/A')}")
                        else:
                            await AgentMessenger.observe(streaming_callback, f"Result: {str(result_data)[:50]}...")
                    else:
                        # Simple result (like calculator)
                        await AgentMessenger.observe(streaming_callback, str(result_data))
                else:
                    # Multiple results - show meaningful summary
                    summaries = []
                    for result_item in results[:3]:  # Show first 3 results
                        # Extract actual result data from parallel execution format
                        result_data = result_item.get("result") if isinstance(result_item, dict) and "result" in result_item else result_item
                        
                        if isinstance(result_data, dict):
                            if "temperature" in result_data:  # Weather
                                summaries.append(f"Weather: {result_data.get('condition', 'N/A')}")
                            elif "datetime" in result_data:  # Timezone  
                                summaries.append(f"Time: {result_data.get('datetime', 'N/A')}")
                            else:
                                summaries.append(f"Data received")
                        else:
                            summaries.append(str(result_data))
                    
                    if len(results) > 3:
                        summaries.append(f"... and {len(results) - 3} more")
                    
                    await AgentMessenger.observe(streaming_callback, "; ".join(summaries))
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
        controller_metrics = {
            "total_executed": len(tool_calls),
            "successful_count": execution_results.get("successful_count", 0),
            "failed_count": execution_results.get("failed_count", 0)
        }
        controller.update_iteration_metrics(controller_metrics, execution_time)
    
    # Always route back to reason for reflection on results
    state["next_node"] = "reason"
    
    return state