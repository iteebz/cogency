from typing import Any, Dict, List
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState, Tool
from cogency.parsing import _extract_tool_call

REASON_PROMPT = (
    "You have access to the following tools:\n{tool_list}\n\n" +
    "To use a tool, respond with a message in the format: TOOL_CALL: <tool_name>(<arg1>=<value1>, <arg2>=<value2>)\n" +
    "For example: TOOL_CALL: calculator(operation=\'add\', num1=5, num2=3) or TOOL_CALL: calculator(operation=\'square_root\', num1=9)\n" +
    "After the tool executes, I will provide the result. You MUST then provide a conversational response to the user, incorporating the tool\'s output. " +
    "If the tool output is an error, explain the error to the user. If the tool output is a result, present it clearly.\n\n"
)

def reason(state: AgentState, llm: LLM, tools: List[Tool]) -> AgentState:
    context = state["context"]
    messages = list(context.messages)

    tool_instructions = ""
    if tools:
        instructions = []
        for tool in tools:
            instructions.append(f"- {tool.name}: {tool.description}")
        tool_instructions = REASON_PROMPT.format(tool_list="\n".join(instructions))

    if tool_instructions:
        messages.insert(0, {"role": "system", "content": tool_instructions})

    result = llm.invoke(messages)

    if isinstance(result, list):
        result_str = " ".join(result) # Join list elements into a single string
    else:
        result_str = result

    context.add_message("assistant", result_str)

    tool_call = _extract_tool_call(result_str)
    if tool_call:
        return {"context": context, "tool_called": True, "task_complete": False, "last_node": "reason"}
    else:
        # If LLM didn't make a tool call, it might be a direct response or an error
        return {"context": context, "tool_called": False, "task_complete": False, "last_node": "reason"}
