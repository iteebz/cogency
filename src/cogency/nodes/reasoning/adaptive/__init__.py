"""Adaptive reasoning control unit - clean public API"""

from cogency.state import summarize_attempts

from .assessment import assess_tools
from .loop import action_fingerprint, detect_fast_loop, detect_loop, should_stop
from .relevance import relevant_context, score_memory_relevance
from .switching import parse_switch, should_switch, switch_mode

__all__ = [
    # Cognitive state
    "summarize_attempts",
    # Mode switching
    "parse_switch",
    "should_switch",
    "switch_mode",
    # Loop detection
    "action_fingerprint",
    "detect_loop",
    "detect_fast_loop",
    "should_stop",
    # Assessment
    "assess_tools",
    # Relevance
    "score_memory_relevance",
    "relevant_context",
]
