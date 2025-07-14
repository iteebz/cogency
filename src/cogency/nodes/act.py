from typing import AsyncIterator, Dict, Any, Optional
from cogency.tools.base import BaseTool
from cogency.llm.base import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.utils.parsing import extract_tool_call, parse_tool_args


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


async def act(state: AgentState, *, tools: Optional[list[BaseTool]] = None) -> AgentState:
    """Non-streaming version for LangGraph compatibility."""
    context = state["context"]

    # Get the last assistant message, which should contain the tool call
    llm_response_content = context.messages[-1]["content"]

    tool_call = extract_tool_call(llm_response_content)
    if tool_call:
        tool_name, tool_args = tool_call
        # Store tool call info temporarily

        raw_args = tool_args.get("raw_args", "")
        parsed_args = parse_tool_args(raw_args)

        # Execute tool
        tool_output = {"error": f"Tool '{tool_name}' not found."}

        for tool in tools:
            if tool.name == tool_name:
                tool_output = await tool.validate_and_run(**parsed_args)
                break

        context.add_message("system", str(tool_output))
        # Store tool execution result for future reference
        context.add_tool_result(tool_name, parsed_args, tool_output)

    return {"context": context, "execution_trace": state["execution_trace"]}
