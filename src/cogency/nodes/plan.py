import json
from typing import AsyncIterator, Dict, Any, Optional
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState

PLAN_PROMPT = """You are an AI assistant. Analyze the user request and respond with ONLY valid JSON.

Available tools: {tool_names}

{injection_point}

Output format (choose one):

{{"action": "direct_response", "answer": "Your answer"}}

{{"action": "tool_needed", "reasoning": "Why tool needed", "strategy": "Which tool", "tool_input": {{"query": "tool specific query"}}}}

Respond with JSON only - no other text."""


async def plan_streaming(state: AgentState, llm: BaseLLM, tools: list[BaseTool], prompt_fragments: Optional[Dict[str, str]] = None, yield_interval: float = 0.0) -> AsyncIterator[Dict[str, Any]]:
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
    
    system_prompt = PLAN_PROMPT.format(tool_names=tool_info, injection_point=prompt_fragments.get("injection_point", ""))
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


async def plan(state: AgentState, llm: BaseLLM, tools: Optional[list[BaseTool]] = None, prompt_fragments: Optional[Dict[str, str]] = None) -> AgentState:
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
    
    # Use prompt_override if provided, otherwise use default PLAN_PROMPT
    current_plan_prompt = PLAN_PROMPT.format(tool_names=tool_info, injection_point=prompt_fragments.get("injection_point", ""))
    system_prompt = current_plan_prompt
    messages.insert(0, {"role": "system", "content": system_prompt})

    llm_response = await llm.invoke(messages)

    # Store the raw response for routing, but don't add to conversation yet
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
