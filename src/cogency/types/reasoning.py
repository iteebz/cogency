from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cogency.utils.parsing import normalize_reasoning


@dataclass
class Reasoning:
    thinking: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    switch_to: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)
    reflect: Optional[str] = None
    plan: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reasoning":
        reasoning_val = data.get("reasoning")
        normalized_reasoning = normalize_reasoning(reasoning_val)

        return cls(
            thinking=data.get("thinking"),
            tool_calls=data.get("tool_calls", []),
            switch_to=data.get("switch_to"),
            reasoning=normalized_reasoning,
            reflect=data.get("reflect"),
            plan=data.get("plan"),
        )
