from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Literal

from cogency.context import Context


# Streaming modes: "raw", "summary", "both"
StreamingMode = Literal["raw", "summary", "both"]


@dataclass
class TraceStep:
    """Single execution step."""
    node: str
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        emojis = {"think": "🤔", "plan": "🧠", "act": "⚡", "reflect": "🔍", "respond": "💬"}
        emoji = emojis.get(self.node, "⚡")
        return f"   {emoji} {self.node.upper().ljust(8)} → {self.summary}"


@dataclass 
class ExecutionTrace:
    """Execution trace - pure data storage."""
    steps: List[TraceStep] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    user_query: str = ""
    
    def add(self, node: str, summary: str):
        """Add step with provided summary."""
        self.steps.append(TraceStep(node, summary))


class AgentState(TypedDict):
    context: Context
    execution_trace: Optional[ExecutionTrace]
