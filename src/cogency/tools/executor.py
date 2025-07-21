"""Tool execution utilities."""
import json
import asyncio
from typing import Dict, Any, List, Tuple, Optional, Union
from cogency.tools.base import BaseTool
from cogency.tools.result import get_data, is_success, get_error
# Using simple dicts for tool calls instead of ToolCall class
from cogency.utils.parsing import parse_json
from cogency.resilience import safe
from cogency.output import emoji


def parse_tool_calls(llm_response_content) -> Optional[List[Dict[str, Any]]]:
    """Extract tool calls from LLM response."""
    # Handle already parsed data (for tests)
    if isinstance(llm_response_content, list):
        return llm_response_content
    elif isinstance(llm_response_content, dict):
        return [llm_response_content]
    
    # Handle string response from LLM
    if not isinstance(llm_response_content, str):
        return None
        
    # Extract JSON data from LLM response using consolidated parsing
    plan_data = parse_json(llm_response_content)
    if not plan_data:
        return None
        
    if plan_data and "tool_calls" in plan_data:
        tool_calls_data = plan_data["tool_calls"]
        if isinstance(tool_calls_data, list):
            return tool_calls_data
    
    return None


async def execute_single_tool(tool_name: str, tool_args: dict, tools: List[BaseTool], context=None) -> Tuple[str, Dict, Any]:
    """Execute a tool with structured error handling."""
    async def _execute():
        for tool in tools:
            if tool.name == tool_name:
                try:
                    # Inject context for user isolation if tool supports it
                    if context:
                        # Check if tool accepts _context parameter
                        import inspect
                        sig = inspect.signature(tool.run)
                        if '_context' in sig.parameters:
                            tool_args["_context"] = context
                        elif any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                            # Only inject if it has **kwargs AND the operation method can handle it
                            # For now, don't inject into tools with dispatch patterns until we have better detection
                            pass
                    result = await tool.execute(**tool_args)
                    return tool_name, tool_args, result
                except Exception as e:
                    return tool_name, tool_args, {"error": f"Tool execution failed: {str(e)}", "success": False}
        raise ValueError(f"Tool '{tool_name}' not found.")
    
    return await _execute()


def needs_sequential(tool_calls: List[Tuple[str, Dict]]) -> bool:
    """Detect dependencies requiring sequential execution."""
    tool_names = [name for name, _ in tool_calls]
    
    file_ops = {"create_file", "write_file", "edit_file", "delete_file"}
    shell_ops = {"run_shell", "execute_command", "bash"}
    
    has_file = any(name in file_ops for name in tool_names)
    has_shell = any(name in shell_ops for name in tool_names)
    
    return has_file and has_shell


async def execute_sequential_tools(tool_calls: List[Tuple[str, Dict]], tools: List[BaseTool], context) -> Dict[str, Any]:
    """Run tools in sequence with error isolation."""
    if not tool_calls:
        return {"success": True, "results": [], "errors": [], "summary": "No tools to execute"}
    
    successes = []
    failures = []
    
    for tool_name, tool_args in tool_calls:
        try:
            result = await execute_single_tool(tool_name, tool_args, tools, context)
            actual_tool_name, actual_args, tool_output = result
            
            if not is_success(tool_output):
                error_msg = get_error(tool_output) or "Unknown error"
                failure_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "error": error_msg,
                    "error_type": "tool_execution_error"
                }
                failures.append(failure_result)
            else:
                success_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "result": get_data(tool_output)
                }
                successes.append(success_result)
                context.add_result(actual_tool_name, actual_args, success_result["result"])
                
        except Exception as e:
            failure_result = {
                "tool_name": tool_name,
                "args": tool_args,
                "error": str(e),
                "error_type": "execution_error"
            }
            failures.append(failure_result)
    
    # Generate summary
    summary_parts = []
    if successes:
        summary_parts.append(f"{len(successes)} tools executed successfully")
    if failures:
        summary_parts.append(f"{len(failures)} tools failed")
    
    summary = "; ".join(summary_parts) if summary_parts else "No tools executed"
    
    # Add execution log to context
    combined_output = "Sequential execution results:\n"
    for success in successes:
        success_emoji = emoji['success']
        combined_output += f"{success_emoji} {success['tool_name']}: {success['result']}\n"
    for failure in failures:
        error_emoji = emoji['error']
        combined_output += f"{error_emoji} {failure['tool_name']}: {failure['error']}\n"
    
    context.add_message("system", combined_output)
    
    return {
        "success": len(failures) == 0,
        "results": successes,
        "errors": failures,
        "summary": summary,
        "total_executed": len(tool_calls),
        "successful_count": len(successes),
        "failed_count": len(failures),
        "execution_mode": "sequential"
    }


async def run_tools(tool_calls: List[Tuple[str, Dict]], tools: List[BaseTool], context) -> Dict[str, Any]:
    """Execute tools with auto parallel/sequential detection."""
    if not tool_calls:
        return {"success": True, "results": [], "errors": [], "summary": "No tools to execute"}
    
    # Smart dependency detection
    if needs_sequential(tool_calls):
        tool_names = [name for name, _ in tool_calls]
        dependency_emoji = emoji['dependency']
        context.add_message("system", f"{dependency_emoji} Dependency detected in tools {tool_names} - switching to sequential execution")
        return await execute_sequential_tools(tool_calls, tools, context)
    
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
        elif isinstance(result, tuple) and len(result) == 3:
            # Normal result - check if tool execution succeeded
            actual_tool_name, actual_args, tool_output = result
            
            if not is_success(tool_output):
                # Tool execution failed
                error_msg = get_error(tool_output) or "Unknown error"
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
                    "result": get_data(tool_output)
                }
                successes.append(success_result)
                
                # Add to context
                context.add_result(actual_tool_name, actual_args, success_result["result"])
        else:
            # Unexpected result type
            failure_result = {
                "tool_name": tool_name,
                "args": tool_args,
                "error": f"Unexpected result type: {type(result)}",
                "error_type": "execution_error"
            }
            failures.append(failure_result)
    
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
        success_emoji = emoji['success']
        combined_output += f"{success_emoji} {success['tool_name']}: {success['result']}\n"
    
    for failure in failures:
        error_emoji = emoji['error']
        combined_output += f"{error_emoji} {failure['tool_name']}: {failure['error']}\n"
    
    context.add_message("system", combined_output)
    
    return {
        "success": len(failures) == 0,
        "results": successes,
        "errors": failures,
        "summary": summary,
        "total_executed": len(tool_calls),
        "successful_count": len(successes),
        "failed_count": len(failures),
        "execution_mode": "parallel"
    }