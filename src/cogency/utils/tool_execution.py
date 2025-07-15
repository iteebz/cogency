"""Tool execution utilities for clean separation of parsing and execution."""
import json
import asyncio
from typing import Dict, Any, List, Tuple, Optional, Union
from cogency.tools.base import BaseTool
from cogency.schemas import ToolCall, MultiToolCall
from cogency.utils.parsing import parse_plan
from cogency.utils import retry
# from cogency.utils.profiling import CogencyProfiler  # Temporarily disabled for faster startup


def parse_tool_call(llm_response_content: str) -> Optional[Union[ToolCall, MultiToolCall]]:
    """Parse tool call from LLM response content.
    
    Args:
        llm_response_content: Raw LLM response 
        
    Returns:
        ToolCall or MultiToolCall object, or None if no tool call found
    """
    plan_data = parse_plan(llm_response_content)
    if plan_data and "tool_call" in plan_data:
        return plan_data["tool_call"]
    return None


@retry(max_attempts=3)
async def execute_single_tool(tool_name: str, tool_args: dict, tools: List[BaseTool]) -> Tuple[str, Dict, Any]:
    """Execute a single tool with given arguments and structured error handling.
    
    Args:
        tool_name: Name of tool to execute
        tool_args: Arguments for tool execution
        tools: Available tools
        
    Returns:
        Tuple of (tool_name, parsed_args, result)
    """
    # profiler = CogencyProfiler()  # Temporarily disabled for faster startup
    
    async def _execute():
        try:
            for tool in tools:
                if tool.name == tool_name:
                    result = await tool.validate_and_run(**tool_args)
                    return tool_name, tool_args, {
                        "success": True,
                        "result": result,
                        "error": None
                    }
            
            # Tool not found - return structured error
            return tool_name, tool_args, {
                "success": False,
                "result": None,
                "error": f"Tool '{tool_name}' not found in available tools",
                "error_type": "tool_not_found"
            }
        
        except Exception as e:
            return tool_name, tool_args, {
                "success": False,
                "result": None,
                "error": str(e),
                "error_type": "execution_error"
            }
    
    # return await profiler.profile_tool_execution(_execute)  # Temporarily disabled
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
    
    # profiler = CogencyProfiler()  # Temporarily disabled for faster startup
    
    async def _execute_parallel():
        # Execute all tools in parallel with error isolation
        tasks = [execute_single_tool(name, args, tools) for name, args in tool_calls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    # Profile the parallel execution
    # results = await profiler.profile_tool_execution(_execute_parallel)  # Temporarily disabled
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
                "error_type": "execution_error"  # Changed from async_error to execution_error
            }
            failures.append(failure_result)
        else:
            # Normal result - check if tool execution succeeded
            actual_tool_name, actual_args, tool_output = result
            
            if isinstance(tool_output, dict) and tool_output.get("success") is False:
                # Tool execution failed
                failure_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "error": tool_output.get("error", "Unknown error"),
                    "error_type": tool_output.get("error_type", "unknown")
                }
                failures.append(failure_result)
            else:
                # Tool execution succeeded
                success_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "result": tool_output.get("result") if isinstance(tool_output, dict) else tool_output
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