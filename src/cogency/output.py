"""Centralized output management for Cogency agents with tracing and formatting"""
from typing import Optional, Callable, List, Dict, Any, Union
import asyncio
from cogency.utils.formatting import truncate, summarize_tool_result


# Emoji mapping - system/workflow emojis only (tools define their own)
emoji = {
    # Core workflow phases
    "preprocess": "🔮",
    "reason": "🧠", 
    "act": "⚡",
    "respond": "💬",
    "memory": "🧠",
    
    # State changes
    "trace": "🔧",
    "error": "❌",
    "success": "✅",
    "thinking": "💭",
    
    # System
    "agent": "🤖",
    "human": "👤",
    "tip": "💡",
    "info": "💡",
    "dependency": "🔒"
}


def tool_emoji(tool_name: str) -> str:
    """Get tool emoji with fallback to lightning bolt"""
    return emoji.get(tool_name.lower(), "⚡")


class Output:
    """Single source of truth for all agent output with tracing and formatting"""
    
    def __init__(self, trace: bool = False, verbose: bool = True, callback: Optional[Callable[[str], None]] = None):
        """Initialize output manager with tracing and verbosity settings"""
        self.tracing = trace
        self.verbose = verbose
        self.callback = callback
        self.entries: List[Dict[str, Any]] = []  # Collected traces
    
    async def trace(self, message: str, node: Optional[str] = None, **kwargs):
        """Record trace entries for debugging and stream to callback if available"""
        if not self.tracing:
            return
            
        # Store trace entry
        entry = {"type": "trace", "message": message, "node": node, **kwargs}
        self.entries.append(entry)
        
        # Stream if callback available
        if self.callback:
            formatted = f"🔮 {message}"
            if node:
                formatted = f"🔮   [{node}] {message}"
            await self.callback(formatted)
    
    async def update(self, message: str, type: str = "info", **kwargs):
        """Display user progress updates with appropriate emoji"""
        if not self.verbose or not self.callback:
            return
            
        emoji = self._emoji_for(type)
        formatted = f"{emoji} {message}"
        await self.callback(formatted)
    
    async def log_tool(self, tool_name: str, result: Any, success: bool = True):
        """Log tool execution with status emoji and formatted result"""
        if not self.verbose or not self.callback:
            return
            
        emoji = tool_emoji(tool_name)
        status = "✅" if success else "❌"
        formatted_result = summarize_tool_result(result) if result else ""
        formatted = f"{emoji} {tool_name} → {status} {formatted_result}"
        await self.callback(formatted)
    
    def _emoji_for(self, type: str) -> str:
        """Map message type to appropriate emoji"""
        emoji_map = {
            "reasoning": "🤔",
            "tool": "🛠️", 
            "response": "💬",
            "error": "⚠️",
            "success": "✅",
            "info": "🤖"
        }
        return emoji_map.get(type, "🤖")
    
    def tool_emoji(self, tool_name: str) -> str:
        """Get tool-specific emoji for display"""
        return tool_emoji(tool_name)
    
    def traces(self) -> List[Dict[str, Any]]:
        """Get copy of all collected trace entries"""
        return self.entries.copy()
    
    def reset_traces(self) -> None:
        """Clear all trace entries"""
        self.entries.clear()
    
    async def send(self, message_type: str, content: str, node: Optional[str] = None, **kwargs):
        """Route messages to appropriate output methods by type"""
        if message_type == "trace":
            await self.trace(content, node=node, **kwargs)
        elif message_type == "update":
            await self.update(content, type="info", **kwargs)
        elif message_type == "tool_execution":
            # Handle tool execution results
            tool_name = kwargs.get("tool_name", "unknown")
            success = kwargs.get("success", True)
            await self.log_tool(tool_name, content, success=success)
        else:
            # Default to update for unknown types
            await self.update(content, type=message_type, **kwargs)