from typing import Any, Dict
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState

RESPOND_PROMPT = (
    "You are an AI assistant. Your goal is to provide a clear and concise conversational response to the user. "
    "Review the entire conversation history, including any tool outputs, and formulate a helpful answer. "
    "Your response should be purely conversational and should NOT include any tool-related syntax like TOOL_CALL: or TOOL_CODE:."
)

def respond(state: AgentState, llm: LLM) -> AgentState:
    context = state["context"]
    messages = list(context.messages)

    messages.insert(0, {"role": "system", "content": RESPOND_PROMPT})

    llm_response = llm.invoke(messages)
    context.add_message("assistant", llm_response)

    return {
        "context": context, 
        "tool_called": state["tool_called"], 
        "task_complete": True, 
        "last_node": "respond"
    }
