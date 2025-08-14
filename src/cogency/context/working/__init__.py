"""Working state subdomain - ephemeral task-scoped cognitive context.

WORKING STATE SCOPE:
Working state is the agent's ephemeral cognitive state during task execution.
It provides structured thinking space for multi-step reasoning and gets cleared
between tasks.

CURRENT IMPLEMENTATION:
Clean 4-field design optimized for natural LLM reasoning flows:
- objective: What we're trying to achieve
- understanding: What we've learned and know  
- approach: How we're tackling this systematically
- discoveries: Key insights, patterns, breakthroughs

ARCHITECTURAL PRINCIPLE:
Working state is cognitive scaffolding for reasoning - temporary, task-scoped,
and designed for natural LLM thought processes without artificial constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WorkingState:
    """Task-scoped cognitive working state for multi-step reasoning.
    
    Clean 4-field design following specification from state.md:
    Provides clear semantic boundaries without fragmenting cognition.
    """
    
    objective: str = ""      # "What we're trying to achieve"
    understanding: str = ""  # "What we've learned and know"  
    approach: str = ""       # "How we're tackling this systematically"
    discoveries: str = ""    # "Key insights, patterns, breakthroughs"


class WorkingContext:
    """Working domain context - cognitive workspace for reasoning."""
    
    def __init__(self, working_state: WorkingState):
        self.working_state = working_state
    
    async def build(self) -> Optional[str]:
        """Build working context from 4-field working state."""
        if not self.working_state:
            return None
            
        parts = []
        
        if self.working_state.objective:
            parts.append(f"OBJECTIVE: {self.working_state.objective}")
            
        if self.working_state.understanding:
            parts.append(f"UNDERSTANDING: {self.working_state.understanding}")
            
        if self.working_state.approach:
            parts.append(f"APPROACH: {self.working_state.approach}")
            
        if self.working_state.discoveries:
            parts.append(f"DISCOVERIES: {self.working_state.discoveries}")
        
        return "\n".join(parts) if parts else None


# Import operations for single-import convenience
from .operations import (
    create_working_state,
    save_working_state,
    load_working_state,
    update_working_state,
)

__all__ = [
    "WorkingState", 
    "WorkingContext",
    # Operations
    "create_working_state",
    "save_working_state",
    "load_working_state",
    "update_working_state",
]