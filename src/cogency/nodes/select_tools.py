"""Node for intelligently selecting a subset of tools."""
from typing import List, Optional

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.types import AgentState
from cogency.utils.trace import trace_node


@trace_node("select_tools")
async def select_tools(state: AgentState, llm: BaseLLM, tools: Optional[List[BaseTool]] = None) -> AgentState:
    """Intelligently select a subset of tools based on the user query."""
    if not tools or len(tools) <= 3:
        state["selected_tools"] = tools or []
        return state

    user_input = state["query"]
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
        state["selected_tools"] = relevant_tools if relevant_tools else tools
        
    except Exception:
        # Fallback to all tools if LLM filtering fails
        state["selected_tools"] = tools

    return state
