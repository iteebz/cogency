"""Tool execution utilities for clean separation of parsing and execution."""
import json
from typing import Dict, Any, List, Tuple, Optional
from cogency.tools.base import BaseTool
from cogency.utils.parsing import extract_tools, parse_tool_args, parse_multi_calls
from cogency.utils import retry


def parse_tool_call(llm_response_content: str) -> Optional[Tuple[str, Dict]]:
    """Parse tool call from LLM response content.
    
    Args:
        llm_response_content: Raw LLM response 
        
    Returns:
        Tuple of (tool_name, tool_args) or None if no tool call found
    """
    tool_call = None
    
    # Try to extract tool call from PLAN node JSON response
    try:
        plan_data = json.loads(llm_response_content)
        if plan_data.get("action") == "tool_needed" and "tool_call" in plan_data:
            tool_call = extract_tools(plan_data["tool_call"])
    except:
        # Fallback to direct extraction from response
        tool_call = extract_tools(llm_response_content)
    
    return tool_call


@retry(max_attempts=3)
async def execute_single_tool(tool_name: str, tool_args: dict, tools: List[BaseTool]) -> Tuple[str, Dict, Any]:
    """Execute a single tool with given arguments.
    
    Args:
        tool_name: Name of tool to execute
        tool_args: Arguments for tool execution
        tools: Available tools
        
    Returns:
        Tuple of (tool_name, parsed_args, result)
    """
    raw_args = tool_args.get("raw_args", "")
    parsed_args = parse_tool_args(raw_args)
    
    for tool in tools:
        if tool.name == tool_name:
            result = await tool.validate_and_run(**parsed_args)
            return tool_name, parsed_args, result
    
    return tool_name, parsed_args, {"error": f"Tool '{tool_name}' not found"}


async def execute_parallel_tools(tool_calls: List[Tuple[str, Dict]], tools: List[BaseTool], context) -> None:
    """Execute multiple tools in parallel and add results to context.
    
    Args:
        tool_calls: List of (tool_name, tool_args) tuples
        tools: Available tools
        context: Context to add results to
    """
    import asyncio
    
    tasks = [execute_single_tool(name, args, tools) for name, args in tool_calls]
    results = await asyncio.gather(*tasks)
    
    # Add all results to context
    combined_output = "Parallel execution results:\n"
    for tool_name, parsed_args, tool_output in results:
        context.add_tool_result(tool_name, parsed_args, tool_output)
        combined_output += f"- {tool_name}: {tool_output}\n"
    
    context.add_message("system", combined_output)