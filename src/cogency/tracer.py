"""Trace formatting and output for clean separation of concerns."""
import time
from typing import List

from cogency.types import ExecutionTrace, OutputMode


class Tracer:
    """Handles formatting and output of execution traces."""

    def __init__(self, trace: ExecutionTrace):
        self.trace = trace

    def _summarize(self) -> str:
        """Generate clean summary from trace entries."""
        summaries = []
        for entry in self.trace.entries:
            msg = entry["message"]
            if any(keyword in msg for keyword in ["Selected", "Executed", "Generated", "Completed"]):
                summaries.append(msg)
        
        if not summaries:
            return "Task completed"
        
        return " → ".join(summaries)

    def _format_trace(self) -> str:
        """Format full trace with icons."""
        icons = {"think": "🤔", "plan": "🧠", "act": "⚡", "reflect": "🔍", "respond": "💬"}
        lines = []
        for entry in self.trace.entries:
            icon = icons.get(entry["node"], "📝")
            lines.append(f"   {icon} {entry['node'].upper():8} → {entry['message']}")
        return "\n".join(lines)

    def _format_full_debug(self) -> str:
        """Format full debug trace (dev mode)."""
        # For now, same as trace mode - can be extended later
        return self._format_trace()

    def output(self, mode: OutputMode):
        """Output trace based on mode."""
        if mode == "summary":
            print(f"✅ {self._summarize()}")
        elif mode == "trace":
            print(self._format_trace())
            print(f"\n✅ Complete")
        elif mode == "dev":
            print(self._format_full_debug())
            print(f"\n✅ Complete")

