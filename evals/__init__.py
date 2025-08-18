"""Beautiful modular evaluation architecture - zero ceremony."""

from .runner import baseline_evaluation
from .core import evaluate_category, judge
from .config import CONFIG
from .storage import save_run
from .generators import security, continuity, reasoning, tooling

__all__ = [
    "baseline_evaluation",
    "evaluate_category", 
    "judge",
    "CONFIG",
    "save_run",
    "security",
    "continuity", 
    "reasoning",
    "tooling"
]