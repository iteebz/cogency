"""Tool execution utilities for clean separation of parsing and execution."""
import json
import asyncio
from typing import Dict, Any, List, Tuple, Optional, Union
from cogency.tools.base import BaseTool
from cogency.tools.result import extract_tool_data, is_tool_success, get_tool_error
from cogency.types import ToolCall, MultiToolCall
from cogency.utils.parsing import extract_json_from_response
from cogency.resilience import retry
from cogency.utils.json import extract_json


def parse_tool_call(llm_response_content) -> Optional[Union[ToolCall, MultiToolCall]]:
    """Parse tool call from LLM response content or pre-parsed data.
    
    Args:
        llm_response_content: Raw LLM response string OR pre-parsed data
        
    Returns:
        ToolCall or MultiToolCall object, or None if no tool call found
    """
    # Handle already parsed data (for tests)
    if isinstance(llm_response_content, (list, dict)):
        # Direct tool call data
        if isinstance(llm_response_content, list):
            if len(llm_response_content) == 1:
                # Single tool call
                call_data = llm_response_content[0]
                return ToolCall(**call_data)
            elif len(llm_response_content) > 1:
                # Multiple tool calls
                calls = [ToolCall(**call_data) for call_data in llm_response_content]
                return MultiToolCall(calls=calls)
        elif isinstance(llm_response_content, dict):
            return ToolCall(**llm_response_content)
        return None
    
    # Handle string response from LLM
    if not isinstance(llm_response_content, str):
        return None
        
    # Extract JSON data from LLM response using consolidated parsing
    plan_data = extract_json_from_response(llm_response_content)
    if not plan_data:
        return None
        
    if plan_data and "tool_call" in plan_data:
        tool_call_data = plan_data["tool_call"]
        
        # Convert dict back to proper ToolCall/MultiToolCall objects
        if isinstance(tool_call_data, dict):
            if "calls" in tool_call_data:
                # MultiToolCall
                calls = [ToolCall(**call_data) for call_data in tool_call_data["calls"]]
                return MultiToolCall(calls=calls)
            else:
                # Single ToolCall
                return ToolCall(**tool_call_data)
        
        # Already a proper object (shouldn't happen with current parsing)
        return tool_call_data
    return None


@retry(max_attempts=3)
async def execute_single_tool(tool_name: str, tool_args: dict, tools: List[BaseTool], context=None) -> Tuple[str, Dict, Any]:
    """Execute a single tool with given arguments and structured error handling.
    
    Args:
        tool_name: Name of tool to execute
        tool_args: Arguments for tool execution
        tools: Available tools
        context: Context to pass to tools for user isolation
        
    Returns:
        Tuple of (tool_name, parsed_args, result)
    """
    async def _execute():
        for tool in tools:
            if tool.name == tool_name:
                try:
                    # Inject context for user isolation if tool supports it
                    if context:
                        # Check if tool accepts _context parameter
                        import inspect
                        sig = inspect.signature(tool.run)
                        if '_context' in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                            tool_args["_context"] = context
                    result = await tool.run(**tool_args)
                    return tool_name, tool_args, result
                except Exception as e:
                    raise
        raise ValueError(f"Tool '{tool_name}' not found.")
    
    return await _execute()


async def execute_parallel_tools(tool_calls: List[Tuple[str, Dict]], tools: List[BaseTool], context) -> Dict[str, Any]:
    """Execute multiple tools in parallel with robust error handling and result aggregation.
    
    Args:
        tool_calls: List of (tool_name, tool_args) tuples
        tools: Available tools
        context: Context to add results to
        
    Returns:
        Aggregated results with success/failure statistics
    """
    if not tool_calls:
        return {"success": True, "results": [], "errors": [], "summary": "No tools to execute"}
    
    async def _execute_parallel():
        # Execute all tools in parallel with error isolation
        tasks = [execute_single_tool(name, args, tools, context) for name, args in tool_calls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    results = await _execute_parallel()
    
    # Process results and separate successes from failures
    successes = []
    failures = []
    
    for i, result in enumerate(results):
        tool_name, tool_args = tool_calls[i]
        
        if isinstance(result, Exception):
            # Handle asyncio.gather exception
            failure_result = {
                "tool_name": tool_name,
                "args": tool_args,
                "error": str(result),
                "error_type": "execution_error"
            }
            failures.append(failure_result)
        else:
            # Normal result - check if tool execution succeeded
            actual_tool_name, actual_args, tool_output = result
            
            if not is_tool_success(tool_output):
                # Tool execution failed
                error_msg = get_tool_error(tool_output) or "Unknown error"
                failure_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "error": error_msg,
                    "error_type": "tool_execution_error"
                }
                failures.append(failure_result)
            else:
                # Tool execution succeeded
                success_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "result": extract_tool_data(tool_output)
                }
                successes.append(success_result)
                
                # Add to context
                context.add_tool_result(actual_tool_name, actual_args, success_result["result"])
    
    # Generate aggregated summary
    summary_parts = []
    if successes:
        summary_parts.append(f"{len(successes)} tools executed successfully")
    if failures:
        summary_parts.append(f"{len(failures)} tools failed")
    
    summary = "; ".join(summary_parts) if summary_parts else "No tools executed"
    
    # Create combined output message for context
    combined_output = "Parallel execution results:\n"
    
    for success in successes:
        combined_output += f"✅ {success['tool_name']}: {success['result']}\n"
    
    for failure in failures:
        combined_output += f"❌ {failure['tool_name']}: {failure['error']}\n"
    
    context.add_message("system", combined_output)
    
    return {
        "success": len(failures) == 0,
        "results": successes,
        "errors": failures,
        "summary": summary,
        "total_executed": len(tool_calls),
        "successful_count": len(successes),
        "failed_count": len(failures)
    }