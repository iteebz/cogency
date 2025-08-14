"""Working state domain types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkingState:
    """Task-scoped cognitive working state for multi-step reasoning.

    Clean 4-field design following specification from state.md:
    - objective: What we're trying to achieve
    - understanding: What we've learned and know
    - approach: How we're tackling this systematically
    - discoveries: Key insights, patterns, breakthroughs
    """

    objective: str = ""
    understanding: str = ""
    approach: str = ""
    discoveries: str = ""
