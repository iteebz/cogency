from typing import Any, Dict
from cogency.context import Context
from cogency.llm import LLM
from cogency.types import Tool
from cogency.types import AgentState

def invoke_llm(state: AgentState, llm: LLM, tools: list[Tool]) -> AgentState:
    context = state["context"]

    messages_for_llm = list(context.messages) # Create a copy

    tool_instructions = ""
    if tools:
        instructions = []
        for tool in tools:
            instructions.append(f"- {tool.name}: {tool.description}")
        tool_instructions = "You have access to the following tools:\n" + "\n".join(instructions) + "\n\n" + \
                           "To use a tool, respond with a message in the format: TOOL_CALL: <tool_name>(<arg1>=<value1>, <arg2>=<value2>)\n" + \
                           "For example: TOOL_CALL: calculator(operation=\'add\', num1=5, num2=3)\n" + \
                           "After the tool executes, I will provide the result. You MUST then provide a conversational response to the user, incorporating the tool\'s output. If the tool output is an error, explain the error to the user. If the tool output is a result, present it clearly.\n\n"

    if tool_instructions:
        messages_for_llm.insert(0, {"role": "system", "content": tool_instructions})

    llm_response_content = llm.invoke(messages_for_llm)
    context.add_message("assistant", llm_response_content)

    return {"context": context, "tool_called": False}
