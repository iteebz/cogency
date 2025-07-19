"""Unified messaging system for agent-user communication."""
from typing import List, Callable, Awaitable


class AgentMessenger:
    """Clean, unified messaging for agent-user communication."""
    
    @staticmethod
    async def memorize(callback: Callable[[str], Awaitable[None]], message: str) -> None:
        """💾 MEMORIZE: Memory extraction/saving."""
        await callback(f"💾 MEMORIZE: {message}\n")
    
    @staticmethod
    async def tooling(callback: Callable[[str], Awaitable[None]], tool_names: List[str]) -> None:
        """🛠️ TOOLING: Tool selection/filtering."""
        if tool_names:
            tools_str = ", ".join(tool_names)
            await callback(f"🛠️ TOOLING: {tools_str}\n\n")
        else:
            await callback("🛠️ TOOLING: No tools needed\n\n")
    
    @staticmethod
    async def reason(callback: Callable[[str], Awaitable[None]], message: str = "Analyzing information and deciding next action") -> None:
        """🧠 REASON: Reasoning/thinking phase."""
        await callback(f"🧠 REASON: {message}\n")
    
    @staticmethod
    async def act(callback: Callable[[str], Awaitable[None]], tool_names: List[str]) -> None:
        """⚡️ ACT: Tool execution phase."""
        if len(tool_names) == 1:
            await callback(f"⚡️ ACT: {tool_names[0]}\n")
        elif len(tool_names) > 1:
            tools_str = ", ".join(tool_names)
            await callback(f"⚡️ ACT: {tools_str}\n")
        else:
            await callback("⚡️ ACT: Executing tools\n")
    
    @staticmethod
    async def observe(callback: Callable[[str], Awaitable[None]], message: str) -> None:
        """👀 OBSERVE: Processing tool results."""
        await callback(f"👀 OBSERVE: {message}\n")
    
    @staticmethod
    async def human_input(callback: Callable[[str], Awaitable[None]], query: str) -> None:
        """👤 HUMAN: User input."""
        await callback(f"👤 HUMAN: {query}\n")
    
    @staticmethod
    async def agent_response(callback: Callable[[str], Awaitable[None]], response: str) -> None:
        """🤖 AGENT: Final response."""
        await callback(f"\n🤖 AGENT: {response}\n")
    
    @staticmethod
    async def spacing(callback: Callable[[str], Awaitable[None]]) -> None:
        """Add spacing between phases."""
        await callback("\n")


# Legacy aliases for compatibility during transition
ThinkingStreamer = AgentMessenger