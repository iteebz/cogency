"""Reason node implementation for stream-first cognitive architecture."""
from typing import AsyncGenerator

from cogency.trace import trace_node
from cogency.utils.interrupt import interruptable
from .base import BaseNode, NodeContext, StreamDelta

REASON_PROMPT = """
You are an AI assistant executing a specific task using available tools.

Available tools:
{tool_schemas}

TOOL USAGE FORMAT:
Use this exact format: TOOL_CALL: <tool_name>(<arg1>=<value1>, <arg2>=<value2>)

Examples:
{tool_examples}

EXECUTION RULES:
1. Use the tool format exactly as shown above
2. Provide only the tool call, no additional text
3. Use quotes for string values: name="John Smith"
4. Use exact parameter names as specified in schemas
5. If you cannot determine the correct parameters, ask for clarification

ERROR HANDLING:
- If tool execution fails, the system will provide error details
- You will then generate a conversational response explaining the issue
"""


class ReasonNode(BaseNode):
    """Reasoning node that generates tool calls for task execution."""
    
    def __init__(self):
        super().__init__(
            name="reason",
            description="Generate tool calls based on task requirements"
        )
    
    async def stream(
        self, 
        ctx: NodeContext, 
        yield_interval: float = 0.0
    ) -> AsyncGenerator[StreamDelta, None]:
        """Stream reasoning process for tool selection."""
        yield {"type": "thinking", "node": self.name, "content": "Analyzing task and selecting appropriate tool...", "data": None, "state": None}
        
        context = ctx.state["context"]

        # Build proper message sequence: include conversation history + current input
        messages = list(context.messages)
        if not any(
            msg.get("role") == "user" and msg.get("content") == context.current_input
            for msg in messages
        ):
            messages.append({"role": "user", "content": context.current_input})

        tool_instructions = ""
        if ctx.tools:
            yield {"type": "thinking", "node": self.name, "content": f"Available tools: {[tool.name for tool in ctx.tools]}", "data": None, "state": None}
            
            # Full tool schemas for precise formatting
            schemas = []
            all_examples = []
            for tool in ctx.tools:
                schemas.append(f"- {tool.name}: {tool.description}")
                schemas.append(f"  Schema: {tool.get_schema()}")
                all_examples.extend([f"  {example}" for example in tool.get_usage_examples()])

            tool_instructions = REASON_PROMPT.format(
                tool_schemas="\n".join(schemas), tool_examples="\n".join(all_examples)
            )

        if tool_instructions:
            messages.insert(0, {"role": "system", "content": tool_instructions})

        # Stream LLM reasoning for tool selection
        yield {"type": "thinking", "node": self.name, "content": "Generating tool call...", "data": None, "state": None}
        response_chunks = []
        async for chunk in ctx.llm.stream(messages, yield_interval=yield_interval):
            yield {"type": "chunk", "node": self.name, "content": chunk, "data": None, "state": None}
            response_chunks.append(chunk)

        result = "".join(response_chunks)

        if isinstance(result, list):
            result_str = " ".join(result)
        else:
            result_str = result

        context.add_message("assistant", result_str)

        # Yield final result
        yield {"type": "result", "node": self.name, "content": None, "data": {"tool_call": result_str}, "state": None}
        
        # Yield final state
        yield {"type": "state", "node": self.name, "content": None, "data": None, "state": {"context": context, "execution_trace": ctx.state["execution_trace"]}}

    @trace_node
    @interruptable
    async def invoke(self, ctx: NodeContext) -> dict:
        """Non-streaming version for LangGraph compatibility."""
        context = ctx.state["context"]

        # Build proper message sequence: include conversation history + current input
        messages = list(context.messages)
        if not any(
            msg.get("role") == "user" and msg.get("content") == context.current_input
            for msg in messages
        ):
            messages.append({"role": "user", "content": context.current_input})

        tool_instructions = ""
        if ctx.tools:
            # Full tool schemas for precise formatting
            schemas = []
            all_examples = []
            for tool in ctx.tools:
                schemas.append(f"- {tool.name}: {tool.description}")
                schemas.append(f"  Schema: {tool.get_schema()}")
                all_examples.extend([f"  {example}" for example in tool.get_usage_examples()])

            tool_instructions = REASON_PROMPT.format(
                tool_schemas="\n".join(schemas), tool_examples="\n".join(all_examples)
            )

        if tool_instructions:
            messages.insert(0, {"role": "system", "content": tool_instructions})

        result = await ctx.llm.invoke(messages)

        if isinstance(result, list):
            result_str = " ".join(result)
        else:
            result_str = result

        context.add_message("assistant", result_str)

        return {"context": context, "execution_trace": ctx.state["execution_trace"]}