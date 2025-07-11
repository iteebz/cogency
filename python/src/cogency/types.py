import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from cogency.context import Context


@dataclass
class ExecutionStep:
    """Individual step in execution trace."""

    node: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionTrace:
    """Simple execution trace for agent reasoning."""

    trace_id: str
    steps: List[ExecutionStep] = field(default_factory=list)

    def add_step(
        self,
        node: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: str,
    ) -> None:
        """Add a new step to the execution trace."""
        step = ExecutionStep(
            node=node,
            input_data=input_data,
            output_data=output_data,
            reasoning=reasoning,
        )
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Export trace for debugging/analysis."""
        return {
            "trace_id": self.trace_id,
            "steps": [
                {
                    "node": step.node,
                    "input_data": step.input_data,
                    "output_data": step.output_data,
                    "reasoning": step.reasoning,
                    "timestamp": step.timestamp.isoformat(),
                }
                for step in self.steps
            ],
        }


class AgentState(TypedDict):
    context: Context
    execution_trace: Optional[ExecutionTrace]
