from typing import Any, Dict
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState

def respond(state: AgentState, llm: LLM) -> AgentState:
    context = state["context"]
    
    # The LLM will generate a conversational response based on the full message history,
    # including any tool outputs.
    final_response_content = llm.invoke(context.messages)
    context.add_message("assistant", final_response_content)

    return {"context": context, "tool_called": False}
