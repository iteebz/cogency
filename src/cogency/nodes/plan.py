from typing import AsyncIterator, Dict, Any
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.utils.interrupt import interruptable

PLAN_PROMPT = """You are an AI assistant. Analyze the user request and respond with ONLY valid JSON.

Available tools: {tool_names}

Rules:
- Math calculations → use calculator tool
- Current info/events → use web search
- File operations → use file_manager tool
- General knowledge → direct response

Output format (choose one):

{{"action": "direct_response", "reasoning": "Brief explanation", "answer": "Your answer"}}

{{"action": "tool_needed", "reasoning": "Why tool needed", "strategy": "Which tool"}}

Respond with JSON only - no other text."""


async def plan_streaming(state: AgentState, llm: BaseLLM, tools: list[BaseTool], yield_interval: float = 0.0) -> AsyncIterator[Dict[str, Any]]:
    """Streaming version of plan node - yields execution steps in real-time.
    
    Args:
        state: Current agent state
        llm: Language model to use
        tools: Available tools for planning
        yield_interval: Minimum time between yields for rate limiting (seconds)
    """
    # Yield initial thinking
    yield {"type": "thinking", "node": "plan", "content": "Analyzing user request and available tools..."}
    # TODO: Implement yield_interval rate limiting when consumer needs it
    # if yield_interval > 0.0:
    #     await asyncio.sleep(yield_interval)
    
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    # Lite tool descriptions for planning decision
    if tools:
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"{tool.name} ({tool.description})")
        tool_info = ", ".join(tool_descriptions)
        yield {"type": "thinking", "node": "plan", "content": f"Available tools: {tool_info}"}
    else:
        tool_info = "no tools"
        yield {"type": "thinking", "node": "plan", "content": "No tools available - will use direct response"}
    
    system_prompt = PLAN_PROMPT.format(tool_names=tool_info)
    messages.insert(0, {"role": "system", "content": system_prompt})

    # Stream LLM response and collect chunks
    yield {"type": "thinking", "node": "plan", "content": "Generating plan decision..."}
    response_chunks = []
    async for chunk in llm.stream(messages, yield_interval=yield_interval):
        yield {"type": "chunk", "node": "plan", "content": chunk}
        response_chunks.append(chunk)
    
    llm_response = "".join(response_chunks)

    # Store the raw response for routing, but don't add to conversation yet
    context.add_message("assistant", llm_response)

    # Yield final result
    yield {"type": "result", "node": "plan", "data": {"decision": llm_response}}
    
    # Yield final state for downstream consumption
    yield {"type": "state", "node": "plan", "state": {"context": context, "execution_trace": state["execution_trace"]}}


@trace_node
@interruptable
async def plan(state: AgentState, llm: BaseLLM, tools: list[BaseTool]) -> AgentState:
    """Non-streaming version for LangGraph compatibility."""
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    # Lite tool descriptions for planning decision
    if tools:
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"{tool.name} ({tool.description})")
        tool_info = ", ".join(tool_descriptions)
    else:
        tool_info = "no tools"
    system_prompt = PLAN_PROMPT.format(tool_names=tool_info)
    messages.insert(0, {"role": "system", "content": system_prompt})

    llm_response = await llm.invoke(messages)

    # Store the raw response for routing, but don't add to conversation yet
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
