from typing import Any, Dict, List

from cogency.context import Context
from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.utils.parsing import extract_tool_call

REASON_PROMPT = """
You have access to the following tools:
{tool_schemas}

To use a tool, respond with a message in the format:
TOOL_CALL: <tool_name>(<arg1>=<value1>, <arg2>=<value2>)

Examples:
{tool_examples}
After the tool executes, I will provide the result.
You MUST then provide a conversational response to user, incorporating tool's output.
If the tool output is an error, explain the error to the user.
If the tool output is a result, present it clearly.
"""


@trace_node
def reason(state: AgentState, llm: BaseLLM, tools: List[BaseTool]) -> AgentState:
    context = state["context"]

    # Build proper message sequence: user question + system instructions
    messages = [{"role": "user", "content": context.current_input}]

    tool_instructions = ""
    if tools:
        # Full tool schemas for precise formatting
        schemas = []
        all_examples = []
        for tool in tools:
            schemas.append(f"- {tool.name}: {tool.description}")
            schemas.append(f"  Schema: {tool.get_schema()}")
            all_examples.extend(
                [f"  {example}" for example in tool.get_usage_examples()]
            )

        tool_instructions = REASON_PROMPT.format(
            tool_schemas="\n".join(schemas), tool_examples="\n".join(all_examples)
        )

    if tool_instructions:
        messages.insert(0, {"role": "system", "content": tool_instructions})

    result = llm.invoke(messages)

    if isinstance(result, list):
        result_str = " ".join(result)  # Join list elements into a single string
    else:
        result_str = result

    context.add_message("assistant", result_str)

    return {"context": context, "execution_trace": state["execution_trace"]}
