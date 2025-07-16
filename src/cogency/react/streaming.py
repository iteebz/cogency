"""Streaming message utilities for ReAct loop phases."""
from typing import List, Union, Callable, Awaitable
from cogency.schemas import ToolCall, MultiToolCall


class ReactStreamer:
    """Utilities for streaming phase-specific messages during ReAct execution."""
    
    @staticmethod
    async def reason_phase(callback: Callable[[str], Awaitable[None]]) -> None:
        """Stream reasoning phase message."""
        await callback("🧠 REASON: Analyzing available information and deciding next action...\n")
    
    @staticmethod
    async def respond_phase(callback: Callable[[str], Awaitable[None]], message: str = "Have sufficient information to provide complete answer") -> None:
        """Stream response phase message."""
        await callback(f"💬 RESPOND: {message}\n")
    
    @staticmethod
    async def act_phase(callback: Callable[[str], Awaitable[None]], tool_call: Union[ToolCall, MultiToolCall, None]) -> None:
        """Stream action phase message with specific tool names."""
        if isinstance(tool_call, MultiToolCall):
            tool_names = [call.name for call in tool_call.calls]
            if len(tool_names) == 1:
                await callback(f"⚡ ACT: Calling {tool_names[0]} tool to gather needed information...\n")
            else:
                tools_str = ", ".join(tool_names)
                await callback(f"⚡ ACT: Calling {tools_str} tools to gather needed information...\n")
        elif isinstance(tool_call, ToolCall):
            await callback(f"⚡ ACT: Calling {tool_call.name} tool to gather needed information...\n")
        else:
            await callback(f"⚡ ACT: Executing tools to gather needed information...\n")
    
    @staticmethod
    async def observe_phase(callback: Callable[[str], Awaitable[None]], 
                          success: bool, tool_call: Union[ToolCall, MultiToolCall, None]) -> None:
        """Stream observation phase message based on execution results."""
        if success:
            if isinstance(tool_call, MultiToolCall):
                tool_names = [call.name for call in tool_call.calls]
                tools_str = ", ".join(tool_names)
                await callback(f"👀 OBSERVE: Successfully gathered data from {tools_str} tools\n")
            elif isinstance(tool_call, ToolCall):
                await callback(f"👀 OBSERVE: Successfully gathered data from {tool_call.name} tool\n")
            else:
                await callback(f"👀 OBSERVE: Successfully gathered data from tools\n")
        else:
            await callback(f"❌ OBSERVE: Tool execution failed, will retry or use available information\n")
    
    @staticmethod
    async def iteration_separator(callback: Callable[[str], Awaitable[None]]) -> None:
        """Add visual separation between iterations."""
        await callback("\n")
    
    @staticmethod
    async def completion_message(callback: Callable[[str], Awaitable[None]]) -> None:
        """Stream final completion message."""
        await callback("\n💬 RESPOND: Sufficient information gathered, preparing final response...\n")