"""Streaming message utilities for ReAct loop phases."""
from typing import List, Union, Callable, Awaitable
from cogency.common.schemas import ToolCall, MultiToolCall
from cogency.utils.formatting import PhaseFormatter


class PhaseStreamer:
    """Utilities for streaming phase-specific messages during ReAct execution."""
    
    @staticmethod
    async def reason_phase(callback: Callable[[str], Awaitable[None]]) -> None:
        """Stream reasoning phase message."""
        await callback(PhaseFormatter.reason("Analyzing available information and deciding next action...") + "\n")
    
    @staticmethod
    async def respond_phase(callback: Callable[[str], Awaitable[None]], message: str = "Have sufficient information to provide complete answer") -> None:
        """Stream response phase message."""
        await callback(PhaseFormatter.respond(message) + "\n")
    
    @staticmethod
    async def act_phase(callback: Callable[[str], Awaitable[None]], tool_call: Union[ToolCall, MultiToolCall, None]) -> None:
        """Stream action phase message with specific tool names."""
        if isinstance(tool_call, MultiToolCall):
            tool_names = [call.name for call in tool_call.calls]
            if len(tool_names) == 1:
                await callback(PhaseFormatter.act(f"Calling {tool_names[0]} tool to gather needed information...") + "\n")
            else:
                tools_str = ", ".join(tool_names)
                await callback(PhaseFormatter.act(f"Calling {tools_str} tools to gather needed information...") + "\n")
        elif isinstance(tool_call, ToolCall):
            await callback(PhaseFormatter.act(f"Calling {tool_call.name} tool to gather needed information...") + "\n")
        else:
            await callback(PhaseFormatter.act("Executing tools to gather needed information...") + "\n")
    
    @staticmethod
    async def observe_phase(callback: Callable[[str], Awaitable[None]], 
                          success: bool, tool_call: Union[ToolCall, MultiToolCall, None]) -> None:
        """Stream observation phase message based on execution results."""
        if success:
            if isinstance(tool_call, MultiToolCall):
                tool_names = [call.name for call in tool_call.calls]
                tools_str = ", ".join(tool_names)
                await callback(PhaseFormatter.observe(f"Successfully gathered data from {tools_str} tools") + "\n")
            elif isinstance(tool_call, ToolCall):
                await callback(PhaseFormatter.observe(f"Successfully gathered data from {tool_call.name} tool") + "\n")
            else:
                await callback(PhaseFormatter.observe("Successfully gathered data from tools") + "\n")
        else:
            await callback(PhaseFormatter.error("Tool execution failed, will retry or use available information") + "\n")
    
    @staticmethod
    async def iteration_separator(callback: Callable[[str], Awaitable[None]]) -> None:
        """Add visual separation between iterations."""
        await callback("\n")
    
    @staticmethod
    async def completion_message(callback: Callable[[str], Awaitable[None]]) -> None:
        """Stream final completion message."""
        await callback("\n" + PhaseFormatter.respond("Sufficient information gathered, preparing final response...") + "\n")
    
    # New methods for PREPARE phase
    @staticmethod
    async def prepare_reason_phase(callback: Callable[[str], Awaitable[None]], message: str) -> None:
        """Stream prepare reasoning phase message."""
        await callback(PhaseFormatter.reason(message) + "\n")
    
    @staticmethod
    async def prepare_memorize_phase(callback: Callable[[str], Awaitable[None]], message: str) -> None:
        """Stream memory extraction/saving phase message."""
        await callback(PhaseFormatter.memorize(message) + "\n")
    
    @staticmethod
    async def prepare_tooling_phase(callback: Callable[[str], Awaitable[None]], message: str) -> None:
        """Stream tool selection/filtering phase message."""
        await callback(PhaseFormatter.tooling(message) + "\n")