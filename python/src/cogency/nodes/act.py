from typing import Any, Dict

from cogency.context import Context
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState
from cogency.utils.parsing import extract_tool_call


@trace_node
def act(state: AgentState, tools: list[BaseTool]) -> AgentState:
    context = state["context"]

    # Get the last assistant message, which should contain the tool call
    llm_response_content = context.messages[-1]["content"]

    tool_call = extract_tool_call(llm_response_content)
    if tool_call:
        tool_name, tool_args = tool_call
        # Store tool call info temporarily

        raw_args = tool_args.get("raw_args", "")
        parsed_args = {}
        if raw_args:
            for arg_pair in raw_args.split(","):
                key, value_str = arg_pair.split("=", 1)
                key = key.strip()
                value_str = value_str.strip()

                # Attempt to convert to int, float, or bool
                if value_str.isdigit():
                    parsed_args[key] = int(value_str)
                elif value_str.replace(".", "", 1).isdigit():
                    parsed_args[key] = float(value_str)
                elif value_str.lower() == "true":
                    parsed_args[key] = True
                elif value_str.lower() == "false":
                    parsed_args[key] = False
                else:
                    # Treat as string, remove surrounding quotes
                    if value_str.startswith("'") and value_str.endswith("'"):
                        parsed_args[key] = value_str[1:-1]
                    elif value_str.startswith('"') and value_str.endswith('"'):
                        parsed_args[key] = value_str[1:-1]
                    else:
                        parsed_args[key] = value_str

        # Execute tool
        tool_output = {"error": f"Tool '{tool_name}' not found."}

        for tool in tools:
            if tool.name == tool_name:
                tool_output = tool.validate_and_run(**parsed_args)
                break

        context.add_message("system", str(tool_output))
        # Store tool execution result for future reference
        context.add_tool_result(tool_name, parsed_args, tool_output)

    return {"context": context, "execution_trace": state["execution_trace"]}
