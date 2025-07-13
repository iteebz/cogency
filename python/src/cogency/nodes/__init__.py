# Legacy function-based nodes for backward compatibility
from .act import act
from .plan import plan
from .reason import reason
from .reflect import reflect
from .respond import respond

# New class-based node interface for pluggable architecture
from .base import BaseNode, StreamDelta, NodeContext
from .plan_node import PlanNode
from .reason_node import ReasonNode
from .act_node import ActNode
from .reflect_node import ReflectNode
from .respond_node import RespondNode

__all__ = [
    # Legacy functions
    "act", "plan", "reason", "reflect", "respond",
    # New pluggable interface
    "BaseNode", "StreamDelta", "NodeContext",
    "PlanNode", "ReasonNode", "ActNode", "ReflectNode", "RespondNode"
]
