from typing import Dict, Any, Optional
from cogency.tools.base import BaseTool
from cogency.llm.base import BaseLLM
from cogency.types import AgentState
from cogency.utils.parsing import extract_tools, parse_tool_args, parse_multi_calls
from cogency.utils import retry, trace


@retry(max_attempts=3)
async def _execute_single(tool_name: str, tool_args: dict, tools: list[BaseTool]) -> tuple:
    """Execute one tool - pure business logic."""
    raw_args = tool_args.get("raw_args", "")
    parsed_args = parse_tool_args(raw_args)
    
    for tool in tools:
        if tool.name == tool_name:
            result = await tool.validate_and_run(**parsed_args)
            return tool_name, parsed_args, result
    
    return tool_name, parsed_args, {"error": f"Tool '{tool_name}' not found"}



async def _execute_parallel(tool_calls: list, tools: list[BaseTool], context) -> None:
    """Execute multiple tools in parallel and add results to context."""
    import asyncio
    
    tasks = [_execute_single(name, args, tools) for name, args in tool_calls]
    results = await asyncio.gather(*tasks)
    
    # Add all results to context
    combined_output = "Parallel execution results:\n"
    for tool_name, parsed_args, tool_output in results:
        context.add_tool_result(tool_name, parsed_args, tool_output)
        combined_output += f"- {tool_name}: {tool_output}\n"
    
    context.add_message("system", combined_output)


@trace
async def act(state: AgentState, *, tools: Optional[list[BaseTool]] = None) -> AgentState:
    """Act node executes tools."""
    
    context = state["context"]

    # Get the last assistant message, which should contain the tool call
    llm_response_content = context.messages[-1]["content"]

    # Try to extract tool call from PLAN node JSON response
    tool_call = None
    try:
        import json
        plan_data = json.loads(llm_response_content)
        if plan_data.get("action") == "tool_needed" and "tool_call" in plan_data:
            tool_call = extract_tools(plan_data["tool_call"])
    except:
        # Fallback to direct extraction from response
        tool_call = extract_tools(llm_response_content)
    
    if tool_call:
        tool_name, tool_args = tool_call
        
        if tool_name == "MULTI_TOOL":
            tool_calls = parse_multi_calls(tool_args.get("multi_calls", ""))
            if len(tool_calls) > 1:
                # Execute parallel tools without streaming
                await _execute_parallel(tool_calls, tools, context)
            elif tool_calls:
                # Single tool in parallel format
                name, args = tool_calls[0]
                tool_name, parsed_args, tool_output = await _execute_single(name, args, tools)
                context.add_message("system", str(tool_output))
                context.add_tool_result(tool_name, parsed_args, tool_output)
        else:
            # Standard single tool execution
            tool_name, parsed_args, tool_output = await _execute_single(tool_name, tool_args, tools)
            context.add_message("system", str(tool_output))
            context.add_tool_result(tool_name, parsed_args, tool_output)

    # Return updated state
    return {"context": context, "execution_trace": state["execution_trace"]}
