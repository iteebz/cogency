from typing import Any, Dict, List
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState, Tool
from cogency.parsing import TOOL_NEEDED_PREFIX, DIRECT_RESPONSE_PREFIX
from cogency.trace import trace_node

PLAN_PROMPT = (
    "You are an AI assistant. Your goal is to help the user. "
    "You have access to the following tools: {tool_names}. "
    "If a tool is available and relevant to the user's request, you MUST use it. "
    "If you can answer directly WITHOUT using a tool, respond with 'DIRECT_RESPONSE: <your answer>'. "
    "If you need a tool, respond with 'TOOL_NEEDED: <brief reason>'."
)

@trace_node
def plan(state: AgentState, llm: LLM, tools: List[Tool]) -> AgentState:
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    tool_names = ", ".join([tool.name for tool in tools]) if tools else "no tools"
    system_prompt = PLAN_PROMPT.format(tool_names=tool_names)
    messages.insert(0, {"role": "system", "content": system_prompt})

    llm_response = llm.invoke(messages)
    context.add_message("assistant", llm_response)

    return {
        "context": context,
        "execution_trace": state["execution_trace"]
    }
