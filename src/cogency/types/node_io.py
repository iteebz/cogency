from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeInput:
    """Base schema for node inputs."""

    iteration: int = 0
    max_iterations: int = 10
    context_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PreprocessInput(NodeInput):
    """Input schema for preprocess node."""

    query: str = ""
    memory_enabled: bool = True


@dataclass
class ReasonInput(NodeInput):
    """Input schema for reason node."""

    selected_tools: List[Dict[str, Any]] = field(default_factory=list)
    react_mode: str = "adaptive"  # fast, deep, adaptive
    cognition_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActInput(NodeInput):
    """Input schema for act node."""

    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    selected_tools: List[Any] = field(default_factory=list)


@dataclass
class RespondInput(NodeInput):
    """Input schema for respond node."""

    reasoning_response: Optional[str] = None
    can_answer_directly: bool = False
    direct_response: Optional[str] = None
    stopping_reason: Optional[str] = None


@dataclass
class NodeOutput:
    """Base schema for node outputs."""

    next_node: str = ""
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class PreprocessOutput(NodeOutput):
    """Output schema for preprocess node."""

    context_enriched: bool = False
    memories_retrieved: int = 0


@dataclass
class ReasonOutput(NodeOutput):
    """Output schema for reason node."""

    tool_calls: Optional[List[Dict[str, Any]]] = None
    reasoning_response: Optional[str] = None
    can_answer_directly: bool = False
    react_mode: str = "fast"
    stopping_reason: Optional[str] = None


@dataclass
class ActOutput(NodeOutput):
    """Output schema for act node."""

    execution_results: Dict[str, Any] = field(default_factory=dict)
    successful_count: int = 0
    total_count: int = 0


@dataclass
class RespondOutput(NodeOutput):
    """Output schema for respond node."""

    final_response: str = ""
    response_generated: bool = True
