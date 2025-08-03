"""Reasoning type definitions - structured thought processes and decision making."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cogency.utils.parsing import _normalize_reasoning


@dataclass
class Reasoning:
    thinking: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    response: Optional[str] = None
    switch_to: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)
    reflect: Optional[str] = None
    plan: Optional[str] = None
    # Cognitive workspace updates - the canonical solution
    updates: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reasoning":
        # Handle case where LLM returns array instead of object
        if isinstance(data, list):
            data = data[0] if data else {}
        elif not isinstance(data, dict):
            data = {}

        reasoning_val = data.get("reasoning")
        normalized_reasoning = _normalize_reasoning(reasoning_val)

        # Tool calls are now raw dictionaries
        tool_calls = data.get("tool_calls", [])

        return cls(
            thinking=data.get("thinking"),
            tool_calls=tool_calls,
            response=data.get("response"),
            switch_to=data.get("switch_to"),
            reasoning=normalized_reasoning,
            reflect=data.get("reflect"),
            plan=data.get("plan"),
            # Cognitive workspace updates
            updates=data.get("updates"),
        )
