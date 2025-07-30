"""Reasoning type definitions - structured thought processes and decision making."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cogency.types.tools import ToolCall
from cogency.utils import normalize_reasoning


@dataclass
class Reasoning:
    thinking: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    switch_to: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)
    reflect: Optional[str] = None
    plan: Optional[str] = None
    # Cognitive workspace updates - the canonical solution
    workspace_update: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reasoning":
        reasoning_val = data.get("reasoning")
        normalized_reasoning = normalize_reasoning(reasoning_val)

        # Convert dict tool_calls to ToolCall objects
        raw_tool_calls = data.get("tool_calls", [])
        tool_calls = [
            ToolCall(name=call["name"], args=call.get("args", {}))
            for call in raw_tool_calls
            if isinstance(call, dict) and "name" in call
        ]

        return cls(
            thinking=data.get("thinking"),
            tool_calls=tool_calls,
            switch_to=data.get("switch_to"),
            reasoning=normalized_reasoning,
            reflect=data.get("reflect"),
            plan=data.get("plan"),
            # Cognitive workspace updates
            workspace_update=data.get("workspace_update"),
        )
