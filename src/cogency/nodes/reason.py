from typing import AsyncIterator, Dict, Any, List, Optional

from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.utils.parsing import prepare_node_messages

REASON_PROMPT = """
You are an AI assistant executing a specific task using available tools.

Available tools:
{tool_schemas}

TOOL USAGE FORMAT:
For single tool: TOOL_CALL: <tool_name>(<arg1>=<value1>, <arg2>=<value2>)
For multiple tools: PARALLEL_CALLS: [<tool_name1>(<args>), <tool_name2>(<args>)]

Examples:
{tool_examples}

EXECUTION RULES:
1. If task requires only ONE tool, use TOOL_CALL format
2. If task requires MULTIPLE tools, use PARALLEL_CALLS format for parallel execution
3. Use quotes for string values: name="John Smith"
4. Use exact parameter names as specified in schemas
5. Analyze the task to determine if tools can be executed in parallel or need sequential execution

PARALLEL EXECUTION:
- Use when tools are independent (e.g., search + calculate)
- Avoid when one tool's output feeds into another
- Maximum efficiency for independent tool calls
"""


async def reason_streaming(state: AgentState, llm: BaseLLM, tools: Optional[List[BaseTool]] = None, prompt_fragments: Optional[Dict[str, str]] = None, yield_interval: float = 0.0) -> AsyncIterator[Dict[str, Any]]:
    """Streaming version of reason node - generates tool calls in real-time.
    
    Args:
        state: Current agent state
        llm: Language model to use
        tools: Available tools for reasoning
        yield_interval: Minimum time between yields for rate limiting (seconds)
    """
    yield {"type": "thinking", "node": "reason", "content": "Analyzing task and selecting appropriate tool..."}
    # TODO: Implement yield_interval rate limiting when consumer needs it
    
    context = state["context"]

    if tools:
        yield {"type": "thinking", "node": "reason", "content": f"Available tools: {[tool.name for tool in tools]}"}
    
    messages = prepare_node_messages(context, tools, REASON_PROMPT)

    # Stream LLM reasoning for tool selection
    yield {"type": "thinking", "node": "reason", "content": "Generating tool call..."}
    response_chunks = []
    async for chunk in llm.stream(messages, yield_interval=yield_interval):
        yield {"type": "chunk", "node": "reason", "content": chunk}
        response_chunks.append(chunk)

    result = "".join(response_chunks)

    if isinstance(result, list):
        result_str = " ".join(result)  # Join list elements into a single string
    else:
        result_str = result

    context.add_message("assistant", result_str)

    # Yield final result
    yield {"type": "result", "node": "reason", "data": {"tool_call": result_str}}
    
    # Yield final state
    yield {"type": "state", "node": "reason", "state": {"context": context, "execution_trace": state["execution_trace"]}}


async def reason(state: AgentState, *, llm: BaseLLM, tools: Optional[List[BaseTool]] = None) -> AgentState:
    """Non-streaming version for LangGraph compatibility."""
    context = state["context"]

    messages = prepare_node_messages(context, tools, REASON_PROMPT)

    result = await llm.invoke(messages)

    if isinstance(result, list):
        result_str = " ".join(result)  # Join list elements into a single string
    else:
        result_str = result

    context.add_message("assistant", result_str)

    return {"context": context, "execution_trace": state["execution_trace"]}
