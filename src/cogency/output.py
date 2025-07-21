"""Clean, unified output management for Cogency agents."""
from typing import Optional, Callable, List, Dict, Any
import asyncio
from cogency.utils.formatting import format_tool_result


# Emoji mapping - system/workflow emojis only (tools define their own)
emoji = {
    # Core workflow phases
    "preprocess": "🔮",
    "reason": "🧠", 
    "act": "⚡",
    "respond": "💬",
    
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


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for a tool name with fallback."""
    return emoji.get(tool_name.lower(), "⚡")




class OutputManager:
    """Unified output manager - single source of truth for all agent output."""
    
    def __init__(self, trace: bool = False, verbose: bool = True, callback: Optional[Callable] = None):
        self.trace_enabled = trace
        self.verbose_enabled = verbose
        self.callback = callback
        self.entries: List[Dict[str, Any]] = []  # Collected traces
    
    async def trace(self, message: str, node: Optional[str] = None, **kwargs):
        """Developer-focused trace output with collection."""
        if not self.trace_enabled:
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
        """User-facing progress updates."""
        if not self.verbose_enabled or not self.callback:
            return
            
        emoji = self._get_emoji(type)
        formatted = f"{emoji} {message}"
        await self.callback(formatted)
    
    async def tool_result(self, tool_name: str, result: Any, success: bool = True):
        """Tool execution results."""
        if not self.verbose_enabled or not self.callback:
            return
            
        emoji = get_tool_emoji(tool_name)
        status = "✅" if success else "❌"
        formatted_result = format_tool_result(result) if result else ""
        formatted = f"{emoji} {tool_name} → {status} {formatted_result}"
        await self.callback(formatted)
    
    def _get_emoji(self, type: str) -> str:
        """Get emoji for message type."""
        emoji_map = {
            "reasoning": "🤔",
            "tool": "🛠️", 
            "response": "💬",
            "error": "⚠️",
            "success": "✅",
            "info": "🤖"
        }
        return emoji_map.get(type, "🤖")
    
    def _get_tool_emoji(self, tool_name: str) -> str:
        """Get emoji for tool."""
        return get_tool_emoji(tool_name)
    
    def get_traces(self) -> List[Dict[str, Any]]:
        """Get collected trace entries."""
        return self.entries.copy()
    
    def clear_traces(self):
        """Clear collected traces."""
        self.entries.clear()
    
    async def send(self, message_type: str, content: str, node: Optional[str] = None, **kwargs):
        """Unified send method - routes to appropriate output methods based on type."""
        if message_type == "trace":
            await self.trace(content, node=node, **kwargs)
        elif message_type == "update":
            await self.update(content, type="info", **kwargs)
        elif message_type == "tool_execution":
            # Handle tool execution results
            tool_name = kwargs.get("tool_name", "unknown")
            success = kwargs.get("success", True)
            await self.tool_result(tool_name, content, success=success)
        else:
            # Default to update for unknown types
            await self.update(content, type=message_type, **kwargs)