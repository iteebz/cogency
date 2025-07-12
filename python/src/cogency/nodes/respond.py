from cogency.llm import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState

RESPOND_PROMPT = """
You are an AI assistant providing the final response to the user.

RESPONSE TASK:
Generate a clear, helpful, and conversational response based on the entire conversation history and tool outputs.

RESPONSE RULES:
1. Be conversational and natural - speak directly to the user
2. Incorporate tool results seamlessly into your response
3. NEVER include technical syntax like TOOL_CALL: or internal JSON
4. If tools provided data, present it clearly and explain its relevance
5. If errors occurred, explain them in user-friendly terms
6. Keep responses concise but complete

TONE: Professional, helpful, and direct. Answer as if you're speaking to a colleague.
"""


@trace_node
def respond(state: AgentState, llm: BaseLLM) -> AgentState:
    context = state["context"]

    # Check if the last message is a direct response JSON
    last_message = context.messages[-1]["content"]

    # Handle case where content might be a list
    if isinstance(last_message, list):
        last_message = last_message[0] if last_message else ""

    try:
        import json

        data = json.loads(last_message)
        if data.get("action") == "direct_response":
            # Replace the JSON with the clean answer
            context.messages[-1]["content"] = data.get("answer", last_message)
            return {"context": context, "execution_trace": state["execution_trace"]}
    except (json.JSONDecodeError, TypeError):
        pass

    # For non-direct responses, use the LLM to generate a response
    messages = list(context.messages)
    messages.insert(0, {"role": "system", "content": RESPOND_PROMPT})

    llm_response = llm.invoke(messages)

    # Replace the last message with the clean response
    context.messages[-1]["content"] = llm_response

    return {"context": context, "execution_trace": state["execution_trace"]}
