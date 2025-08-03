"""Triaged data types."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Triaged:
    memory: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    memory_type: Optional[str] = None
    mode: Optional[str] = None
    selected_tools: List[str] = field(default_factory=list)
    reasoning: Optional[str] = None
