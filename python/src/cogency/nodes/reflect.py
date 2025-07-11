from typing import Any, Dict, List
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState
from cogency.parsing import TASK_COMPLETE_PREFIX, CONTINUE_TASK_PREFIX
from cogency.trace import trace_node

REFLECT_PROMPT = (
    "You are an AI assistant whose sole purpose is to evaluate the outcome of the previous action. "
    "Review the last tool output (if any) and the conversation history. "
    "Decide if the user's request has been fully addressed. "
    "If the task is complete, respond with 'TASK_COMPLETE: <brief summary>'. "
    "If more actions are needed, respond with 'CONTINUE_TASK: <brief reason>'. "
    "If there was an error, respond with 'ERROR_OCCURRED: <description of error>'."
)

@trace_node
def reflect(state: AgentState, llm: LLM) -> AgentState:
    context = state["context"]
    messages = list(context.messages)

    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    llm_response = llm.invoke(messages)
    context.add_message("assistant", llm_response)

    return {
        "context": context,
        "execution_trace": state["execution_trace"]
    }
