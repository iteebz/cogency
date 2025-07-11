from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState

PLAN_PROMPT = """
You are an AI assistant analyzing user requests to determine the appropriate action.

Available tools: {tool_names}

CRITICAL RULES:
1. For ANY mathematical calculation (including basic arithmetic), you MUST use the calculator tool
2. For current information, trends, or recent events, you MUST use web search
3. Only provide direct responses for general knowledge questions that don't require computation or current data

Your output MUST be valid JSON with no additional text:
- Direct response: {{"action": "direct_response", "reasoning": "This is general knowledge that doesn't require tools", "answer": "<your complete answer>"}}
- Tool needed: {{"action": "tool_needed", "reasoning": "<specific reason why tool is needed>", "strategy": "<which tool and how you'll use it>"}}

IMPORTANT: Be decisive. If unsure, prefer using tools over direct responses.
"""


@trace_node
def plan(state: AgentState, llm: BaseLLM, tools: list[BaseTool]) -> AgentState:
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    # Lite tool descriptions for planning decision
    if tools:
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"{tool.name} ({tool.description})")
        tool_info = ", ".join(tool_descriptions)
    else:
        tool_info = "no tools"
    system_prompt = PLAN_PROMPT.format(tool_names=tool_info)
    messages.insert(0, {"role": "system", "content": system_prompt})

    llm_response = llm.invoke(messages)

    # Store the raw response for routing, but don't add to conversation yet
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
