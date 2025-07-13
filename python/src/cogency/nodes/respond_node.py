"""Respond node implementation for stream-first cognitive architecture."""
from typing import AsyncGenerator

from cogency.trace import trace_node
from cogency.utils.interrupt import interruptable
from .base import BaseNode, NodeContext, StreamDelta

RESPOND_PROMPT = """
You are an AI assistant providing the final response to the user.

RESPONSE TASK:
Generate a clear, helpful, and conversational response based on the entire
conversation history and tool outputs.

RESPONSE RULES:
1. Be conversational and natural - speak directly to the user
2. Incorporate tool results seamlessly into your response
3. NEVER include technical syntax like TOOL_CALL: or internal JSON
4. If tools provided data, present it clearly and explain its relevance
5. If errors occurred, explain them in user-friendly terms
6. Keep responses concise but complete

TONE: Professional, helpful, and direct. Answer as if you're speaking to a colleague.
"""


class RespondNode(BaseNode):
    """Response node that generates final user-facing responses."""
    
    def __init__(self):
        super().__init__(
            name="respond",
            description="Generate final conversational response for user"
        )
    
    async def stream(
        self, 
        ctx: NodeContext, 
        yield_interval: float = 0.0
    ) -> AsyncGenerator[StreamDelta, None]:
        """Stream response generation with real-time output."""
        yield {"type": "thinking", "node": self.name, "content": "Preparing final response for user...", "data": None, "state": None}
        
        context = ctx.state["context"]

        # Check if the last message is a direct response JSON
        last_message = context.messages[-1]["content"]

        # Handle case where content might be a list
        if isinstance(last_message, list):
            last_message = last_message[0] if last_message else ""

        try:
            import json

            data = json.loads(last_message)
            if data.get("action") == "direct_response":
                yield {"type": "thinking", "node": self.name, "content": "Using direct response from planning", "data": None, "state": None}
                # Replace the JSON with the clean answer
                clean_answer = data.get("answer", last_message)
                context.messages[-1]["content"] = clean_answer
                
                yield {"type": "result", "node": self.name, "content": None, "data": {"response": clean_answer}, "state": None}
                yield {"type": "state", "node": self.name, "content": None, "data": None, "state": {"context": context, "execution_trace": ctx.state["execution_trace"]}}
                return
        except (json.JSONDecodeError, TypeError):
            pass

        # For non-direct responses, use the LLM to generate a response
        yield {"type": "thinking", "node": self.name, "content": "Generating conversational response...", "data": None, "state": None}
        
        messages = list(context.messages)
        messages.insert(0, {"role": "system", "content": RESPOND_PROMPT})

        # Stream the final response generation
        response_chunks = []
        async for chunk in ctx.llm.stream(messages, yield_interval=yield_interval):
            yield {"type": "chunk", "node": self.name, "content": chunk, "data": None, "state": None}
            response_chunks.append(chunk)

        llm_response = "".join(response_chunks)

        # Replace the last message with the clean response
        context.messages[-1]["content"] = llm_response

        yield {"type": "result", "node": self.name, "content": None, "data": {"response": llm_response}, "state": None}
        yield {"type": "state", "node": self.name, "content": None, "data": None, "state": {"context": context, "execution_trace": ctx.state["execution_trace"]}}

    @trace_node
    @interruptable
    async def invoke(self, ctx: NodeContext) -> dict:
        """Non-streaming version for LangGraph compatibility."""
        context = ctx.state["context"]

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
                return {"context": context, "execution_trace": ctx.state["execution_trace"]}
        except (json.JSONDecodeError, TypeError):
            pass

        # For non-direct responses, use the LLM to generate a response
        messages = list(context.messages)
        messages.insert(0, {"role": "system", "content": RESPOND_PROMPT})

        llm_response = await ctx.llm.invoke(messages)

        # Replace the last message with the clean response
        context.messages[-1]["content"] = llm_response

        return {"context": context, "execution_trace": ctx.state["execution_trace"]}