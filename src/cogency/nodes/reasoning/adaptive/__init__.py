"""Adaptive reasoning control unit - clean public API"""

# Core cognitive state management
# Tool assessment
from .assessment import assess_tools
from .cognition import init_cognition, summarize_attempts, track_failure, update_cognition

# Loop detection and action fingerprinting
from .loop import action_fingerprint, detect_fast_loop, detect_loop

# LLM-based relevance scoring
from .relevance import relevant_context, score_memory_relevance

# Mode switching logic
from .switching import (
    get_switching_criteria,
    parse_switch,
    should_switch,
    switch_mode,
    switch_prompt,
)

__all__ = [
    # Cognitive state
    "init_cognition",
    "update_cognition",
    "track_failure",
    "summarize_attempts",
    # Mode switching
    "get_switching_criteria",
    "parse_switch",
    "should_switch",
    "switch_mode",
    "switch_prompt",
    # Loop detection
    "action_fingerprint",
    "detect_loop",
    "detect_fast_loop",
    # Assessment
    "assess_tools",
    # Relevance
    "score_memory_relevance",
    "relevant_context",
]
