"""Enhanced cognitive reasoning subsystem."""

from .cognition import (
    init_cognition, 
    update_cognition, 
    summarize_attempts, 
    track_failure
)
from .loop_detection import action_fingerprint, detect_loop
from .assessment import assess_tools
from .prompts import REASON_PROMPT

__all__ = [
    "init_cognition",
    "update_cognition", 
    "summarize_attempts",
    "track_failure",
    "action_fingerprint",
    "detect_loop",
    "assess_tools",
    "REASON_PROMPT"
]