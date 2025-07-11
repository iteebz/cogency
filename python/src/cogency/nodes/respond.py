from typing import Any, Dict

from cogency.context import Context
from cogency.llm import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState

RESPOND_PROMPT = """
You are an AI assistant.
Your goal is to provide a clear and concise conversational response to the user.
Review the entire conversation history, including any tool outputs, and formulate a helpful answer.
Your response should be purely conversational and should NOT include any tool-related syntax like TOOL_CALL: or TOOL_CODE:.
"""


@trace_node
def respond(state: AgentState, llm: BaseLLM) -> AgentState:
    context = state["context"]

    # Check if the last message is a direct response JSON
    last_message = context.messages[-1]["content"]
    try:
        import json

        data = json.loads(last_message)
        if data.get("action") == "direct_response":
            # Replace the JSON with the clean answer
            context.messages[-1]["content"] = data.get("answer", last_message)
            return {"context": context, "execution_trace": state["execution_trace"]}
    except json.JSONDecodeError:
        pass

    # For non-direct responses, use the LLM to generate a response
    messages = list(context.messages)
    messages.insert(0, {"role": "system", "content": RESPOND_PROMPT})

    llm_response = llm.invoke(messages)

    # Replace the last message with the clean response
    context.messages[-1]["content"] = llm_response

    return {"context": context, "execution_trace": state["execution_trace"]}
