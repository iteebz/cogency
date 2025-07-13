"""Reflect node implementation for stream-first cognitive architecture."""
from typing import AsyncGenerator

from cogency.trace import trace_node
from cogency.utils.interrupt import interruptable
from .base import BaseNode, NodeContext, StreamDelta

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


class ReflectNode(BaseNode):
    """Reflection node that evaluates task completion status."""
    
    def __init__(self):
        super().__init__(
            name="reflect",
            description="Evaluate task completion and determine next steps"
        )
    
    async def stream(
        self, 
        ctx: NodeContext, 
        yield_interval: float = 0.0
    ) -> AsyncGenerator[StreamDelta, None]:
        """Stream reflection analysis for task completion assessment."""
        yield {"type": "thinking", "node": self.name, "content": "Evaluating task completion status...", "data": None, "state": None}
        
        context = ctx.state["context"]
        messages = list(context.messages)

        yield {"type": "thinking", "node": self.name, "content": "Analyzing conversation history and tool outputs...", "data": None, "state": None}
        
        messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

        # Stream the reflection analysis
        response_chunks = []
        async for chunk in ctx.llm.stream(messages, yield_interval=yield_interval):
            yield {"type": "chunk", "node": self.name, "content": chunk, "data": None, "state": None}
            response_chunks.append(chunk)

        llm_response = "".join(response_chunks)
        context.add_message("assistant", llm_response)
        
        yield {"type": "result", "node": self.name, "content": None, "data": {"assessment": llm_response}, "state": None}
        yield {"type": "state", "node": self.name, "content": None, "data": None, "state": {"context": context, "execution_trace": ctx.state["execution_trace"]}}

    @trace_node
    @interruptable
    async def invoke(self, ctx: NodeContext) -> dict:
        """Non-streaming version for LangGraph compatibility."""
        context = ctx.state["context"]
        messages = list(context.messages)

        messages.insert(0, {"role": "system", "content": REFLECT_PROMPT})

        llm_response = await ctx.llm.invoke(messages)
        context.add_message("assistant", llm_response)

        return {"context": context, "execution_trace": ctx.state["execution_trace"]}