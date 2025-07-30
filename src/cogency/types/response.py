"""Response type definitions - structured agent output with metadata and tool results."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Response:
    text: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
