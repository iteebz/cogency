from typing import Any, Dict, List

from cogency.context import Context
from cogency.llm import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState

REFLECT_PROMPT = """
You are an AI assistant whose sole purpose is to evaluate the outcome of the previous action.
Review the last tool output (if any) and the conversation history. 
Decide if the user's request has been fully addressed. 
Most simple requests (like calculations, questions) should be marked as complete after successful tool execution. 
Respond with JSON in one of these formats:
- If task is complete: {"status": "complete", "assessment": "<brief summary>"}
- If more actions needed: {"status": "continue", "reasoning": "<brief reason>"}
- If error occurred: {"status": "error", "description": "<error description>"}
"""


@trace_node
def reflect(state: AgentState, llm: BaseLLM) -> AgentState:
    context = state["context"]
    messages = list(context.messages)

    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    llm_response = llm.invoke(messages)
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
