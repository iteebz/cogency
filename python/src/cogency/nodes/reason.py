from typing import Any, Dict, List
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import AgentState, Tool
from cogency.utils.parsing import extract_tool_call
from cogency.trace import trace_node

REASON_PROMPT = (
    "You have access to the following tools:\n{tool_list}\n\n" +
    "To use a tool, respond with a message in the format: TOOL_CALL: <tool_name>(<arg1>=<value1>, <arg2>=<value2>)\n" +
    "For example: TOOL_CALL: calculator(operation=\'add\', num1=5, num2=3) or TOOL_CALL: calculator(operation=\'square_root\', num1=9)\n" +
    "After the tool executes, I will provide the result. You MUST then provide a conversational response to the user, incorporating the tool\'s output. " +
    "If the tool output is an error, explain the error to the user. If the tool output is a result, present it clearly.\n\n"
)

@trace_node
def reason(state: AgentState, llm: LLM, tools: List[Tool]) -> AgentState:
    context = state["context"]
    
    # Build proper message sequence: user question + system instructions
    messages = [{"role": "user", "content": context.current_input}]
    
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

    return {
        "context": context,
        "execution_trace": state["execution_trace"]
    }
