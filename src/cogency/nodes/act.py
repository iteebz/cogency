from typing import AsyncIterator, Dict, Any, Optional
from cogency.tools.base import BaseTool
from cogency.llm.base import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.utils.parsing import extract_tool_call, parse_tool_args, parse_parallel_calls


async def act_streaming(state: AgentState, tools: Optional[list[BaseTool]] = None, prompt_fragments: Optional[Dict[str, str]] = None, yield_interval: float = 0.0) -> AsyncIterator[Dict[str, Any]]:
    """Streaming version of act node - executes tools with real-time feedback.
    
    Args:
        state: Current agent state
        tools: Available tools for execution
        yield_interval: Minimum time between yields for rate limiting (seconds)
    """
    yield {"type": "thinking", "node": "act", "content": "Parsing tool call from reasoning..."}
    
    context = state["context"]

    # Get the last assistant message, which should contain the tool call
    llm_response_content = context.messages[-1]["content"]

    tool_call = extract_tool_call(llm_response_content)
    if tool_call:
        tool_name, tool_args = tool_call
        yield {"type": "thinking", "node": "act", "content": f"Executing tool: {tool_name}"}
        
        raw_args = tool_args.get("raw_args", "")
        if raw_args:
            yield {"type": "thinking", "node": "act", "content": f"Parsing arguments: {raw_args}"}
        parsed_args = parse_tool_args(raw_args)

        # Execute tool
        yield {"type": "thinking", "node": "act", "content": f"Running {tool_name} with args: {parsed_args}"}
        
        tool_found = False
        tool_output = {"error": f"Tool '{tool_name}' not found."}
        for tool in tools:
            if tool.name == tool_name:
                tool_found = True
                yield {"type": "tool_call", "node": "act", "data": {"tool": tool_name, "args": parsed_args}}
                try:
                    tool_output = await tool.validate_and_run(**parsed_args)
                except Exception as e:
                    tool_output = {"error": f"Tool execution failed: {str(e)}"}
                    yield {"type": "error", "node": "act", "content": f"Tool execution failed: {str(e)}"}
                break

        if not tool_found:
            yield {"type": "error", "node": "act", "content": f"Tool '{tool_name}' not found"}

        yield {"type": "thinking", "node": "act", "content": f"Tool execution completed"}
        
        context.add_message("system", str(tool_output))
        context.add_tool_result(tool_name, parsed_args, tool_output)
        
        # Yield tool execution result
        yield {"type": "result", "node": "act", "data": {"tool": tool_name, "args": parsed_args, "output": tool_output}}
    else:
        yield {"type": "thinking", "node": "act", "content": "No valid tool call found"}
        yield {"type": "result", "node": "act", "data": {"error": "No tool call to execute"}}

    # Yield final state
    yield {"type": "state", "node": "act", "state": {"context": context, "execution_trace": state["execution_trace"]}}


async def _execute_single(tool_name: str, tool_args: dict, tools: list[BaseTool]) -> tuple:
    """Execute one tool and return results."""
    raw_args = tool_args.get("raw_args", "")
    parsed_args = parse_tool_args(raw_args)
    
    for tool in tools:
        if tool.name == tool_name:
            try:
                result = await tool.validate_and_run(**parsed_args)
                return tool_name, parsed_args, result
            except Exception as e:
                return tool_name, parsed_args, {"error": f"Tool execution failed: {str(e)}"}
    
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


async def act(state: AgentState, *, tools: Optional[list[BaseTool]] = None) -> AgentState:
    """Execute tools - single or parallel based on REASON decision."""
    context = state["context"]
    llm_response = context.messages[-1]["content"]
    
    tool_call = extract_tool_call(llm_response)
    if not tool_call:
        return {"context": context, "execution_trace": state["execution_trace"]}
    
    tool_name, tool_args = tool_call
    
    if tool_name == "PARALLEL":
        tool_calls = parse_parallel_calls(tool_args.get("parallel_calls", ""))
        if len(tool_calls) > 1:
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
    
    return {"context": context, "execution_trace": state["execution_trace"]}
