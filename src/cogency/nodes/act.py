from typing import Dict, Any, Optional
from cogency.tools.base import BaseTool
from cogency.llm.base import BaseLLM
from cogency.types import AgentState
from cogency.utils.tool_execution import parse_tool_call, execute_single_tool, execute_parallel_tools
from cogency.schemas import ToolCall, MultiToolCall
from cogency.utils.trace import trace_node


@trace_node("act")
async def act(state: AgentState, *, tools: Optional[list[BaseTool]] = None) -> AgentState:
    """Act node executes tools."""
    
    context = state["context"]

    # Get the last assistant message, which should contain the tool call
    llm_response_content = context.messages[-1]["content"]

    # Parse tool call using utility
    tool_call = parse_tool_call(llm_response_content)
    
    if tool_call:
        if isinstance(tool_call, MultiToolCall):
            # Execute parallel tools
            tool_calls_for_execution = [(call.name, call.args) for call in tool_call.calls]
            await execute_parallel_tools(tool_calls_for_execution, tools, context)
        elif isinstance(tool_call, ToolCall):
            # Standard single tool execution
            tool_name, parsed_args, tool_output = await execute_single_tool(tool_call.name, tool_call.args, tools)
            context.add_message("system", str(tool_output))
            context.add_tool_result(tool_name, parsed_args, tool_output)

    # Return updated state
    return {"context": context, "tool_results": context.tool_results if hasattr(context, 'tool_results') else []}