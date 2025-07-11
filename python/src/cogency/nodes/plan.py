from typing import Any, Dict, List
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState, Tool
from cogency.trace import trace_node

PLAN_PROMPT = (
    "You are an AI assistant. Your goal is to help the user. "
    "You have access to the following tools: {tool_names}. "
    "CRITICAL: For ANY math calculation, you MUST use the calculator tool, even for simple math. "
    "NEVER do math in your head - always use the calculator tool. "
    "Only give direct responses for non-math questions. "
    "Respond with JSON in one of these formats:\n"
    "- If you can answer directly WITHOUT tools: {{\"action\": \"direct_response\", \"answer\": \"<your answer>\"}}\n"
    "- If you need a tool: {{\"action\": \"tool_needed\", \"strategy\": \"<brief reason>\"}}"
)

@trace_node
def plan(state: AgentState, llm: LLM, tools: List[Tool]) -> AgentState:
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    tool_names = ", ".join([tool.name for tool in tools]) if tools else "no tools"
    system_prompt = PLAN_PROMPT.format(tool_names=tool_names)
    messages.insert(0, {"role": "system", "content": system_prompt})

    llm_response = llm.invoke(messages)

    # Store the raw response for routing, but don't add to conversation yet
    context.add_message("assistant", llm_response)

    return {
        "context": context,
        "execution_trace": state["execution_trace"]
    }
