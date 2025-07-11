from cogency.llm import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState

REFLECT_PROMPT = """
You are an AI assistant evaluating task completion status.

ANALYSIS TASK:
Review the conversation history and tool outputs to determine if the user's request has been fully addressed.

DECISION CRITERIA:
- COMPLETE: Tool executed successfully and produced the expected result
- CONTINUE: Additional tools or steps are needed to fully address the request
- ERROR: Tool execution failed or produced an error that needs handling

Your output MUST be valid JSON with no additional text:
- Task complete: {{"status": "complete", "assessment": "<brief summary of what was accomplished>"}}
- More work needed: {{"status": "continue", "reasoning": "<specific reason why more work is needed>"}}
- Error occurred: {{"status": "error", "description": "<clear description of the error>"}}

IMPORTANT: Be decisive. Most single-tool requests should be marked complete after successful execution.
"""


@trace_node
def reflect(state: AgentState, llm: BaseLLM) -> AgentState:
    context = state["context"]
    messages = list(context.messages)

    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    llm_response = llm.invoke(messages)
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
