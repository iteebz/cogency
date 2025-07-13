"""Plan node implementation for stream-first cognitive architecture."""
from typing import AsyncGenerator

from cogency.trace import trace_node
from cogency.utils.interrupt import interruptable
from .base import BaseNode, NodeContext, StreamDelta

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


class PlanNode(BaseNode):
    """Planning node that decides between direct response or tool usage."""
    
    def __init__(self):
        super().__init__(
            name="plan",
            description="Analyze user request and decide execution strategy"
        )
    
    async def stream(
        self, 
        ctx: NodeContext, 
        yield_interval: float = 0.0
    ) -> AsyncGenerator[StreamDelta, None]:
        """Stream planning decision with real-time reasoning."""
        yield {"type": "thinking", "node": self.name, "content": "Analyzing user request and available tools...", "data": None, "state": None}
        
        context = ctx.state["context"]
        messages = context.messages + [{"role": "user", "content": context.current_input}]

        # Build tool descriptions for planning decision
        if ctx.tools:
            tool_descriptions = []
            for tool in ctx.tools:
                tool_descriptions.append(f"{tool.name} ({tool.description})")
            tool_info = ", ".join(tool_descriptions)
            yield {"type": "thinking", "node": self.name, "content": f"Available tools: {tool_info}", "data": None, "state": None}
        else:
            tool_info = "no tools"
            yield {"type": "thinking", "node": self.name, "content": "No tools available - will use direct response", "data": None, "state": None}
        
        system_prompt = PLAN_PROMPT.format(tool_names=tool_info)
        messages.insert(0, {"role": "system", "content": system_prompt})

        # Stream LLM response and collect chunks
        yield {"type": "thinking", "node": self.name, "content": "Generating plan decision...", "data": None, "state": None}
        response_chunks = []
        async for chunk in ctx.llm.stream(messages, yield_interval=yield_interval):
            yield {"type": "chunk", "node": self.name, "content": chunk, "data": None, "state": None}
            response_chunks.append(chunk)
        
        llm_response = "".join(response_chunks)

        # Store the raw response for routing, but don't add to conversation yet
        context.add_message("assistant", llm_response)

        # Yield final result
        yield {"type": "result", "node": self.name, "content": None, "data": {"decision": llm_response}, "state": None}
        
        # Yield final state for downstream consumption
        yield {"type": "state", "node": self.name, "content": None, "data": None, "state": {"context": context, "execution_trace": ctx.state["execution_trace"]}}

    @trace_node
    @interruptable
    async def invoke(self, ctx: NodeContext) -> dict:
        """Non-streaming version for LangGraph compatibility."""
        context = ctx.state["context"]
        messages = context.messages + [{"role": "user", "content": context.current_input}]

        # Build tool descriptions for planning decision
        if ctx.tools:
            tool_descriptions = []
            for tool in ctx.tools:
                tool_descriptions.append(f"{tool.name} ({tool.description})")
            tool_info = ", ".join(tool_descriptions)
        else:
            tool_info = "no tools"
        
        system_prompt = PLAN_PROMPT.format(tool_names=tool_info)
        messages.insert(0, {"role": "system", "content": system_prompt})

        llm_response = await ctx.llm.invoke(messages)

        # Store the raw response for routing, but don't add to conversation yet
        context.add_message("assistant", llm_response)

        return {"context": context, "execution_trace": ctx.state["execution_trace"]}