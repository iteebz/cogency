from typing import Any, Dict
from cogency.context import Context
from cogency.types import Tool
from cogency.types import AgentState
from cogency.utils.parsing import extract_tool_call
from cogency.trace import trace_node

@trace_node
def act(state: AgentState, tools: list[Tool]) -> AgentState:
    context = state["context"]
    tool_was_called = False

    # Get the last assistant message, which should contain the tool call
    llm_response_content = context.messages[-1]["content"]

    tool_call = extract_tool_call(llm_response_content)
    if tool_call:
        tool_name, tool_args = tool_call
        context.tool_call_details = {"name": tool_name, "args": tool_args}
        tool_was_called = True

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
                elif value_str.replace('.', '', 1).isdigit():
                    parsed_args[key] = float(value_str)
                elif value_str.lower() == 'true':
                    parsed_args[key] = True
                elif value_str.lower() == 'false':
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
                try:
                    tool_output = tool.run(**parsed_args)
                except TypeError as e:
                    tool_output = {"error": f"Tool argument error: {e}. Please check the arguments provided to the tool."}
                except ValueError as e:
                    tool_output = {"error": f"Tool data error: {e}. The tool received invalid data."}
                except Exception as e:
                    tool_output = {"error": f"An unexpected error occurred during tool execution: {type(e).__name__}: {e}"}
                break

        context.add_message("system", str(tool_output))
        # Clear tool_call_details after use
        context.tool_call_details = None

    return {
        "context": context,
        "execution_trace": state["execution_trace"]
    }
