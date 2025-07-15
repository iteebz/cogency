"""Tool execution utilities for clean separation of parsing and execution."""
import json
from typing import Dict, Any, List, Tuple, Optional, Union
from cogency.tools.base import BaseTool
from cogency.schemas import ToolCall, MultiToolCall
from cogency.utils.parsing import parse_plan
from cogency.utils import retry


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
    """Execute a single tool with given arguments.
    
    Args:
        tool_name: Name of tool to execute
        tool_args: Arguments for tool execution
        tools: Available tools
        
    Returns:
        Tuple of (tool_name, parsed_args, result)
    """
    
    for tool in tools:
        if tool.name == tool_name:
            result = await tool.validate_and_run(**tool_args)
            return tool_name, tool_args, result
    
    return tool_name, tool_args, {"error": f"Tool '{tool_name}' not found"}


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