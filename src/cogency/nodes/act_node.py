"""Act node implementation for stream-first cognitive architecture."""
import asyncio
from typing import AsyncGenerator

from cogency.trace import trace_node
from cogency.utils.interrupt import interruptable
from cogency.utils.parsing import extract_tool_call
from .base import BaseNode, NodeContext, StreamDelta


class ActNode(BaseNode):
    """Action node that executes tools based on reasoning output."""
    
    def __init__(self):
        super().__init__(
            name="act",
            description="Execute tool calls and return results"
        )
    
    async def stream(
        self, 
        ctx: NodeContext, 
        yield_interval: float = 0.0
    ) -> AsyncGenerator[StreamDelta, None]:
        """Stream tool execution with real-time feedback."""
        yield {"type": "thinking", "node": self.name, "content": "Parsing tool call from reasoning...", "data": None, "state": None}
        
        context = ctx.state["context"]

        # Get the last assistant message, which should contain the tool call
        llm_response_content = context.messages[-1]["content"]

        tool_call = extract_tool_call(llm_response_content)
        if tool_call:
            tool_name, tool_args = tool_call
            yield {"type": "thinking", "node": self.name, "content": f"Executing tool: {tool_name}", "data": None, "state": None}
            
            raw_args = tool_args.get("raw_args", "")
            parsed_args = {}
            if raw_args:
                yield {"type": "thinking", "node": self.name, "content": f"Parsing arguments: {raw_args}", "data": None, "state": None}
                
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
            yield {"type": "thinking", "node": self.name, "content": f"Running {tool_name} with args: {parsed_args}", "data": None, "state": None}
            
            tool_found = False
            tool_output = {"error": f"Tool '{tool_name}' not found."}
            for tool in ctx.tools:
                if tool.name == tool_name:
                    tool_found = True
                    yield {"type": "tool_call", "node": self.name, "content": None, "data": {"tool": tool_name, "args": parsed_args}, "state": None}
                    try:
                        tool_output = await tool.validate_and_run(**parsed_args)
                    except Exception as e:
                        tool_output = {"error": f"Tool execution failed: {str(e)}"}
                        yield {"type": "error", "node": self.name, "content": f"Tool execution failed: {str(e)}", "data": None, "state": None}
                    break

            if not tool_found:
                yield {"type": "error", "node": self.name, "content": f"Tool '{tool_name}' not found", "data": None, "state": None}

            yield {"type": "thinking", "node": self.name, "content": f"Tool execution completed", "data": None, "state": None}
            
            context.add_message("system", str(tool_output))
            context.add_tool_result(tool_name, parsed_args, tool_output)
            
            # Yield tool execution result
            yield {"type": "result", "node": self.name, "content": None, "data": {"tool": tool_name, "args": parsed_args, "output": tool_output}, "state": None}
        else:
            yield {"type": "thinking", "node": self.name, "content": "No valid tool call found", "data": None, "state": None}
            yield {"type": "result", "node": self.name, "content": None, "data": {"error": "No tool call to execute"}, "state": None}

        # Yield final state
        yield {"type": "state", "node": self.name, "content": None, "data": None, "state": {"context": context, "execution_trace": ctx.state["execution_trace"]}}
    

    @trace_node
    @interruptable
    async def invoke(self, ctx: NodeContext) -> dict:
        """Non-streaming version for LangGraph compatibility."""
        context = ctx.state["context"]

        # Get the last assistant message, which should contain the tool call
        llm_response_content = context.messages[-1]["content"]

        tool_call = extract_tool_call(llm_response_content)
        if tool_call:
            tool_name, tool_args = tool_call

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

            for tool in ctx.tools:
                if tool.name == tool_name:
                    try:
                        tool_output = await tool.validate_and_run(**parsed_args)
                    except Exception as e:
                        tool_output = {"error": f"Tool execution failed: {str(e)}"}
                    break

            context.add_message("system", str(tool_output))
            context.add_tool_result(tool_name, parsed_args, tool_output)

        return {"context": context, "execution_trace": ctx.state["execution_trace"]}