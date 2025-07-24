"""Simple output system - thinking states and tool feedback only."""

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union


class Output:
    """Unified output system - three message types: state, update, trace."""

    def __init__(
        self,
        trace: bool = False,
        verbose: bool = True,
        callback: Optional[Union[Callable[[str], None], Callable[[str], Awaitable[None]]]] = None,
    ):
        self.tracing = trace
        self.verbose = verbose
        self.callback = callback
        self.entries: List[Dict[str, Any]] = []  # For debugging

    async def state(self, state_name: str, content: str = "", **kwargs) -> None:
        """Show thinking states for UX feedback - users like seeing this."""
        if not self.callback:
            return

        # Show reasoning states for user feedback
        if state_name == "reasoning":
            if "DEEP" in content or "deep" in content.lower():
                message = "\n🧠 Thinking deeply...\n"
            elif "FAST" in content or "fast" in content.lower():
                message = "\n⚡️ Thinking fast...\n"
            else:
                message = "\n🧠 Thinking...\n"
            await self.callback(message)
            await asyncio.sleep(0)
        elif state_name == "responding":
            # Responding is silent - just the response content
            pass

    async def update(self, content: str, type: str = "info", **kwargs) -> None:
        """Simple updates - memory saves and thinking content."""
        if not self.callback:
            return

        # Memory saves and thinking content only
        if "saved:" in content.lower():
            message = f"\n💾 {content}"
        elif "selected tools:" in content.lower():
            message = f"\n🛠️ {content}"
        elif content:  # Thinking text from reasoning
            message = f"\n{content}"
        else:
            return  # Skip empty updates

        await self.callback(message)
        await asyncio.sleep(0)

    async def trace(self, content: str, node: Optional[str] = None, **kwargs) -> None:
        """Developer debugging traces - clean visual flow."""
        if not self.tracing:
            return

        # Store for debugging
        self.entries.append({"type": "trace", "message": content, "node": node, **kwargs})

        if self.callback:
            # Enhanced trace formatting with better visual hierarchy
            if "ROUTING" in content:
                # Flow routing - use directional arrows
                message = f"\n  🔄 {content}"
            elif node == "flow":
                message = f"\n  🌊 {content}"
            elif node == "preprocess":
                message = f"\n  🔮 {content}"
            elif node == "reason":
                message = f"\n  🧠 {content}"
            elif node == "act":
                message = f"\n  ⚡️ {content}"
            else:
                node_part = f"[{node}] " if node else ""
                message = f"\n  ➡️ {node_part}{content}"
            await self.callback(message)

    async def tool_execution_summary(
        self, tool_name: str, result: Any, success: bool = True
    ) -> None:
        """Tool execution summary - enhanced visual feedback."""
        if not self.callback:
            return

        # Enhanced tool emojis and styling
        tool_emojis = {
            "code": "💻",
            "files": "📁",
            "shell": "🔧",
            "search": "🔍",
            "scrape": "🌐",
            "calculator": "🧮",
            "recall": "🧠",
        }
        emoji = tool_emojis.get(tool_name.lower(), "⚡")

        summary = self._summarize_result(result) if result else ""

        if success and summary:
            # Success with meaningful output
            if tool_name.lower() == "shell" and "✓" in summary:
                # Shell commands that succeed - make them pop
                message = f"{emoji} {summary}"
            elif tool_name.lower() == "files" and "Created" in summary:
                # File creation success
                message = f"{emoji} {summary}"
            else:
                message = f"{emoji} {tool_name}({summary})"
        elif success:
            message = f"{emoji} {tool_name} ✓"
        else:
            message = f"{emoji} {tool_name} ❌ {summary if summary else 'Failed'}"

        await self.update(message, type="tool")

    def _summarize_result(self, result: Any) -> str:
        """Summarize tool results for display."""
        from cogency.utils.results import Result

        # Handle Result objects directly
        if isinstance(result, Result):
            if not result.success:
                return f"❌ {result.error}"
            # Summarize successful result data
            result = result.data

        # Handle basic types
        if isinstance(result, str):
            return result[:97] + "..." if len(result) > 100 else result
        elif isinstance(result, list):
            return f"📋 {len(result)} items"
        elif isinstance(result, dict):
            # Legacy dict handling - will be removed as migration completes
            if "error" in result:
                return f"❌ {result['error']}"
            elif "output" in result:
                output = str(result["output"])
                return output[:100] + "..." if len(output) > 100 else output

        return "✅ Complete"
