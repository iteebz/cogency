import json
import re
from typing import Dict, Any, Optional
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState
from cogency.utils import validate_tools, trace

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


async def _subset_tools(user_input: str, tools: list[BaseTool], llm: BaseLLM) -> list[BaseTool]:
    """Let LLM intelligently select relevant tools."""
    if len(tools) <= 3:  # Don't filter if few tools
        return tools
        
    tool_list = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
    
    prompt = f"""Request: "{user_input}"

Tools:
{tool_list}

Return JSON with relevant tools only:
{{"relevant_tools": ["tool1", "tool2"]}}"""

    try:
        response = await llm.invoke([{"role": "user", "content": prompt}])
        import json
        result = json.loads(response)
        relevant_names = set(result.get("relevant_tools", []))
        
        # Filter to selected tools
        relevant_tools = [tool for tool in tools if tool.name in relevant_names]
        return relevant_tools if relevant_tools else tools
        
    except Exception:
        # Fallback to all tools if LLM filtering fails
        return tools




@trace
async def plan(state: AgentState, llm: BaseLLM, tools: Optional[list[BaseTool]] = None, prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
    """Plan node determines execution strategy."""
    
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    # Intelligent tool subsetting
    if tools:
        relevant_tools = await _subset_tools(context.current_input, tools, llm)
        
        tool_descriptions = []
        for tool in relevant_tools:
            tool_descriptions.append(f"{tool.name} ({tool.description})")
        tool_info = ", ".join(tool_descriptions)
            
        # Store selected tools for downstream nodes
        state["selected_tools"] = relevant_tools
    else:
        tool_info = "no tools"
        state["selected_tools"] = []
    
    system_prompt = PLAN_PROMPT.format(tool_names=tool_info, injection_point=prompt_fragments.get("injection_point", ""))
    messages.insert(0, {"role": "system", "content": system_prompt})

    # Get LLM response
    llm_response = await llm.invoke(messages)

    # Validate tool calls if present
    if tools:
        validated_response = validate_tools(llm_response, tools)
        if validated_response != llm_response:
            llm_response = validated_response

    # Store the raw response for routing
    context.add_message("assistant", llm_response)
    
    # Return updated state
    return {"context": context, "execution_trace": state["execution_trace"]}
