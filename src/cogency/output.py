"""Output management for Cogency agents.

This module provides a centralized output management system for Cogency agents,
handling tracing, user updates, and tool execution logging with consistent formatting.
"""
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
    """Get tool emoji with fallback.
    
    Args:
        tool_name: Name of the tool to get emoji for
        
    Returns:
        str: Emoji character for the tool or default lightning bolt
    """
    return emoji.get(tool_name.lower(), "⚡")


class Output:
    """Single source of truth for all agent output.
    
    This class centralizes all output operations for Cogency agents, including:
    - Trace collection for debugging and development
    - User-facing progress updates
    - Tool execution logging
    - Consistent formatting and emoji usage
    
    Attributes:
        tracing: Whether to collect trace entries
        verbose: Whether to display user-facing updates
        callback: Optional streaming callback function
        entries: List of collected trace entries
    """
    
    def __init__(self, trace: bool = False, verbose: bool = True, callback: Optional[Callable[[str], None]] = None):
        """Initialize Output manager.
        
        Args:
            trace: Whether to collect trace entries
            verbose: Whether to display user-facing updates
            callback: Optional streaming callback function for real-time updates
        """
        self.tracing = trace
        self.verbose = verbose
        self.callback = callback
        self.entries: List[Dict[str, Any]] = []  # Collected traces
    
    async def trace(self, message: str, node: Optional[str] = None, **kwargs):
        """Developer trace output with collection.
        
        Records trace entries for debugging and development purposes.
        If a callback is provided and tracing is enabled, also streams
        the trace message to the callback.
        
        Args:
            message: The trace message to record
            node: Optional node identifier (e.g., "reason", "act")
            **kwargs: Additional metadata to store with the trace
            
        Returns:
            None
        """
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
        """Display user progress updates.
        
        Shows user-facing progress updates if verbose mode is enabled
        and a callback is available.
        
        Args:
            message: The update message to display
            type: Message type for emoji selection (info, reasoning, tool, etc.)
            **kwargs: Additional parameters (unused)
            
        Returns:
            None
        """
        if not self.verbose or not self.callback:
            return
            
        emoji = self._emoji_for(type)
        formatted = f"{emoji} {message}"
        await self.callback(formatted)
    
    async def log_tool(self, tool_name: str, result: Any, success: bool = True):
        """Log tool execution with status.
        
        Displays tool execution results with appropriate formatting
        and emoji indicators.
        
        Args:
            tool_name: Name of the executed tool
            result: Result data from tool execution
            success: Whether the tool execution was successful
            
        Returns:
            None
        """
        if not self.verbose or not self.callback:
            return
            
        emoji = tool_emoji(tool_name)
        status = "✅" if success else "❌"
        formatted_result = summarize_tool_result(result) if result else ""
        formatted = f"{emoji} {tool_name} → {status} {formatted_result}"
        await self.callback(formatted)
    
    def _emoji_for(self, type: str) -> str:
        """Map message type to emoji.
        
        Args:
            type: Message type identifier
            
        Returns:
            str: Emoji character for the message type
        """
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
        """Get tool-specific emoji.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            str: Emoji character for the tool
        """
        return tool_emoji(tool_name)
    
    def traces(self) -> List[Dict[str, Any]]:
        """Get trace entries.
        
        Returns:
            List[Dict[str, Any]]: Copy of all collected trace entries
        """
        return self.entries.copy()
    
    def reset_traces(self) -> None:
        """Clear all trace entries.
        
        Returns:
            None
        """
        self.entries.clear()
    
    async def send(self, message_type: str, content: str, node: Optional[str] = None, **kwargs):
        """Route messages to appropriate output methods by type.
        
        Unified interface for sending different types of messages through
        the output system.
        
        Args:
            message_type: Type of message ("trace", "update", "tool_execution", etc.)
            content: Message content
            node: Optional node identifier
            **kwargs: Additional parameters for specific message types
            
        Returns:
            None
        """
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