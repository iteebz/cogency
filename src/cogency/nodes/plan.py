import json
import re
from typing import Dict, Any, Optional
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState
from cogency.utils import validate_tools
from cogency.utils.trace import trace_node

PLAN_PROMPT = """Tools: {tool_names}

{injection_point}

Decide if tools needed or can respond directly.

If tools needed, generate VALID tool calls using EXACT tool names:
- Single tool: SINGLE_TOOL: tool_name(arg1="value1", arg2="value2")
- Multiple tools: MULTI_TOOL: [tool1(args), tool2(args)]

CRITICAL: Only use tool names from the available tools list above. 
Invalid tool names will cause execution failure.

JSON output format (REQUIRED):
{{"action": "direct_response", "answer": "your answer"}} OR
{{"action": "tool_needed", "tool_call": "SINGLE_TOOL: tool_name(args)"}} OR
{{"action": "tool_needed", "tool_call": "MULTI_TOOL: [tool1(args), tool2(args)]"}}

VALIDATION: Before outputting, verify:
1. Tool names match available tools exactly
2. Arguments follow proper syntax: arg="value"
3. JSON is valid and properly formatted"""



@trace_node("plan")
async def plan(state: AgentState, llm: BaseLLM, tools: Optional[list[BaseTool]] = None, prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """Plan node determines execution strategy."""
    
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    # Use pre-selected tools from state or fall back to all tools
    selected_tools = state.get("selected_tools", tools or [])
    
    if selected_tools:
        tool_descriptions = []
        for tool in selected_tools:
            tool_descriptions.append(f"{tool.name} ({tool.description})")
        tool_info = ", ".join(tool_descriptions)
    else:
        tool_info = "no tools"
    
    system_prompt = PLAN_PROMPT.format(tool_names=tool_info, injection_point=prompt_fragments.get("injection_point", "") if prompt_fragments else "")
    messages.insert(0, {"role": "system", "content": system_prompt})

    # Get LLM response
    llm_response = await llm.invoke(messages)

    # Validate tool calls if present
    if selected_tools:
        validated_response = validate_tools(llm_response, selected_tools)
        if validated_response != llm_response:
            llm_response = validated_response

    # Store the raw response for routing
    context.add_message("assistant", llm_response)
    
    # Return updated state
    return {"context": context, "plan_response": llm_response, "selected_tools": selected_tools}