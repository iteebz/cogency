from typing import AsyncIterator, Dict, Any, Optional, List
from cogency.llm import BaseLLM
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.tools.base import BaseTool

REFLECT_PROMPT = """
You are an AI assistant evaluating task completion and FILTERING OUT BULLSHIT.

ANALYSIS TASK:
1. Review conversation history and tool outputs
2. FILTER OUT useless/irrelevant results  
3. Keep only data that DIRECTLY answers the user's request
4. Determine if task is complete

FILTERING CRITERIA:
- Remove tool execution metadata, debug info, status messages
- Remove redundant or duplicate information
- Keep only the ESSENTIAL data that answers the user's question
- Summarize complex tool outputs into clear, actionable insights

DECISION CRITERIA:
- COMPLETE: Essential information obtained and filtered
- CONTINUE: Still missing key information to answer the request
- ERROR: Tool failure that blocks completion

Your output MUST be valid JSON:
{{"status": "complete", "filtered_result": "<clean, focused answer>", "reasoning": "<why task is complete>"}}
{{"status": "continue", "missing": "<what's still needed>", "reasoning": "<why more work needed>"}}
{{"status": "error", "error": "<clear error description>"}}

FOCUS: Return only what the user ACTUALLY needs, not tool execution bullshit.
"""


async def reflect_streaming(state: AgentState, llm: BaseLLM, tools: Optional[List[BaseTool]] = None, prompt_fragments: Optional[Dict[str, str]] = None, yield_interval: float = 0.0) -> AsyncIterator[Dict[str, Any]]:
    """Streaming version of reflect node - evaluates task completion in real-time.
    
    Args:
        state: Current agent state
        llm: Language model to use
        yield_interval: Minimum time between yields for rate limiting (seconds)
    """
    yield {"type": "thinking", "node": "reflect", "content": "Evaluating task completion and filtering out bullshit..."}
    
    context = state["context"]
    messages = list(context.messages)

    yield {"type": "thinking", "node": "reflect", "content": "Analyzing results and removing useless metadata..."}
    
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


async def reflect(state: AgentState, *, llm: BaseLLM) -> AgentState:
    """Non-streaming version for LangGraph compatibility."""
    context = state["context"]
    messages = list(context.messages)

    messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

    llm_response = await llm.invoke(messages)
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
