from typing import Any, Dict, List
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState

REFLECT_PROMPT = (
    "You are an AI assistant whose sole purpose is to evaluate the outcome of the previous action. "
    "Review the last tool output (if any) and the conversation history. "
    "Decide if the user's request has been fully addressed. "
    "If the task is complete, respond with 'TASK_COMPLETE: <brief summary>'. "
    "If more actions are needed, respond with 'CONTINUE_TASK: <brief reason>'. "
    "If there was an error, respond with 'ERROR_OCCURRED: <description of error>'."
)

def reflect(state: AgentState, llm: LLM) -> AgentState:
    context = state["context"]
    messages = list(context.messages)

    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    result = llm.invoke(messages)
    
    context.add_message("assistant", result)

    if result.startswith("TASK_COMPLETE:"):
        return {"context": context, "tool_called": False, "task_complete": True, "last_node": "reflect"}
    else:
        # If not complete, assume more actions are needed or an.error occurred
        return {"context": context, "tool_called": False, "task_complete": False, "last_node": "reflect"}
