"""Core reasoning utilities - reusable across any architecture."""
from .adaptive import ReasonController, StoppingCriteria, ReasoningMetrics, StoppingReason
from .complexity import analyze_query_complexity, get_complexity_category, estimate_iterations_needed
from .parsing import ReactResponseParser
from .loop_detection import LoopDetector, LoopDetectionConfig, LoopType

__all__ = [
    "ReasonController",
    "StoppingCriteria", 
    "ReasoningMetrics",
    "StoppingReason",
    "analyze_query_complexity",
    "get_complexity_category",
    "estimate_iterations_needed",
    "ReactResponseParser",
    "LoopDetector",
    "LoopDetectionConfig",
    "LoopType",
]