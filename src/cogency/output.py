"""Centralized output management for Cogency agents with tracing and formatting"""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from cogency.utils import summarize_tool_result, tool_emoji
from cogency.utils.emoji import emoji, cognitive_states, format_cognitive_state


class Output:
    """Single source of truth for all agent output with tracing and formatting"""

    def __init__(
        self,
        trace: bool = False,
        verbose: bool = True,
        callback: Optional[Union[Callable[[str], None], Callable[[str], Awaitable[None]]]] = None,
    ):
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
            # Split on | for separate trace lines
            parts = message.split(" | ")
            for part in parts:
                indent = "    " if node else ""
                formatted = f"\n\n{indent}➡️ [{node}] {part.strip()}" if node else f"\n\n➡️ {part.strip()}"
                await self.callback(formatted)

    async def update(self, message: str, type: str = "info", node: Optional[str] = None, **kwargs):
        """Display user progress updates with clear cognitive state indicators"""
        if not self.callback:
            return

        # Detect cognitive state from message content and format cleanly
        formatted_message = self._format_cognitive_update(message, node, **kwargs)
        await self.callback(f"\n{formatted_message}")
    
    def _format_cognitive_update(self, message: str, node: Optional[str] = None, **kwargs) -> str:
        """Format update messages with appropriate cognitive state indicators"""
        
        # Deep mode phases - use specific cognitive states
        if message.startswith("🤔 REFLECTION:"):
            content = message.replace("🤔 REFLECTION:", "").strip()
            return format_cognitive_state("reflecting", content)
        elif message.startswith("📋 PLANNING:"):
            content = message.replace("📋 PLANNING:", "").strip()
            return format_cognitive_state("planning", content)
        elif message.startswith("🎯 DECISION:"):
            content = message.replace("🎯 DECISION:", "").strip()
            return format_cognitive_state("deciding", content)
        
        # General thinking/reasoning
        elif message.startswith("💭") or "Thinking through" in message:
            content = message.replace("💭", "").strip()
            return format_cognitive_state("thinking", content)
            
        # Tool preparation - extract tool list and format nicely
        elif "Tools:" in message:
            tools_part = message.split("Tools:")[-1].strip()
            content = f"\n{tools_part}"
            return format_cognitive_state("tool_selection", content)
            
        # Mode switching
        elif "Escalate to DEEP MODE" in message or "Mode switch:" in message:
            return format_cognitive_state("switching", message)
            
        # Node-based states
        elif node == "preprocess":
            return format_cognitive_state("preprocessing", message)
        elif node == "act":
            # Special handling for act node - show tool names with emojis
            tool_names = kwargs.get("tool_names", [])
            tools = kwargs.get("tools", [])
            if tool_names:
                tool_list = []
                for name in tool_names:
                    # Find tool by name to get emoji
                    tool = next((t for t in tools if t.name == name), None)
                    emoji = tool.emoji if tool and hasattr(tool, 'emoji') else "⚡"
                    tool_list.append(f"{emoji} {name}")
                content = f"\n{', '.join(tool_list)}"
                return format_cognitive_state("executing", content)
            return format_cognitive_state("executing", message)
        elif node == "reason":
            return format_cognitive_state("thinking", message)
        elif node == "respond":
            return format_cognitive_state("responding", message)
            
        # Default: clean message without state indicator
        return message

    async def tool_execution_summary(self, tool_name: str, result: Any, success: bool = True):
        """Display concise tool execution summaries."""
        if not self.callback:
            return

        icon = tool_emoji(tool_name)
        status = "✅" if success else "❌"
        formatted_result = summarize_tool_result(result) if result else ""
        formatted = f"\n{icon} {tool_name} → {status} {formatted_result}"
        await self.callback(formatted)

    async def send(self, message_type: str, content: str, node: Optional[str] = None, **kwargs):
        """Route messages to appropriate output methods by type"""
        if message_type == "trace":
            await self.trace(content, node=node, **kwargs)
        elif message_type == "update":
            await self.update(content, type="info", node=node, **kwargs)
        elif message_type == "tool_execution_summary":
            tool_name = kwargs.get("tool_name", "unknown")
            success = kwargs.get("success", True)
            await self.tool_execution_summary(tool_name, content, success=success)
        else:
            # Default to update for unknown types
            await self.update(content, type=message_type, node=node, **kwargs)
