"""Cogency State container."""

from dataclasses import dataclass, field
from typing import Any, Dict

from cogency.context import Context
from cogency.output import Output


@dataclass
class State:
    """Agent state with dict-like access."""

    # WORLD-CLASS MINIMALISM
    context: Context
    query: str
    output: Output = field(default_factory=Output)
    flow: Dict[str, Any] = field(default_factory=dict)  # Ephemeral workflow data

    # Dict-like access for compatibility - checks flow first, then core fields
    def __getitem__(self, key: str) -> Any:
        if key in self.flow:
            return self.flow[key]
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key in ["context", "query", "output", "flow"]:
            setattr(self, key, value)
        else:
            self.flow[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.flow:
            return self.flow[key]
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.flow or hasattr(self, key)
