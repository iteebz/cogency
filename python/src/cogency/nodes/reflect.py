from typing import AsyncIterator, Dict, Any
from cogency.llm import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.utils.interrupt import interruptable

REFLECT_PROMPT = """
You are an AI assistant evaluating task completion status.

ANALYSIS TASK:
Review conversation history and tool outputs to determine if user's request has been addressed.

DECISION CRITERIA:
- COMPLETE: Tool executed successfully and produced the expected result
- CONTINUE: Additional tools or steps are needed to fully address the request
- ERROR: Tool execution failed or produced an error that needs handling

Your output MUST be valid JSON with no additional text:
- Task complete: {{"status": "complete", "assessment": "<brief summary of what was accomplished>"}}
- More work needed: {{"status": "continue", "reasoning": "<specific reason why
  more work is needed>"}}
- Error occurred: {{"status": "error", "description": "<clear description of the error>"}}

IMPORTANT: Be decisive. Most single-tool requests should be marked complete
after successful execution.
"""


async def reflect_streaming(state: AgentState, llm: BaseLLM, yield_interval: float = 0.0) -> AsyncIterator[Dict[str, Any]]:
    """Streaming version of reflect node - evaluates task completion in real-time.
    
    Args:
        state: Current agent state
        llm: Language model to use
        yield_interval: Minimum time between yields for rate limiting (seconds)
    """
    yield {"type": "thinking", "node": "reflect", "content": "Evaluating task completion status..."}
    
    context = state["context"]
    messages = list(context.messages)

    yield {"type": "thinking", "node": "reflect", "content": "Analyzing conversation history and tool outputs..."}
    
    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    # Stream the reflection analysis
    response_chunks = []
    async for chunk in llm.stream(messages, yield_interval=yield_interval):
        yield {"type": "chunk", "node": "reflect", "content": chunk}
        response_chunks.append(chunk)

    llm_response = "".join(response_chunks)
    context.add_message("assistant", llm_response)
    
    yield {"type": "result", "node": "reflect", "data": {"assessment": llm_response}}
    yield {"type": "state", "node": "reflect", "state": {"context": context, "execution_trace": state["execution_trace"]}}


@trace_node
@interruptable
async def reflect(state: AgentState, llm: BaseLLM) -> AgentState:
    """Non-streaming version for LangGraph compatibility."""
    context = state["context"]
    messages = list(context.messages)

    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    llm_response = await llm.invoke(messages)
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
