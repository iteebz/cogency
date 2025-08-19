"""Beautiful modular evaluation architecture - zero ceremony."""

from .config import CONFIG
from .core import evaluate_category, judge
from .generators import continuity, reasoning, security, tooling
from .runner import run_baseline
from .storage import save_run

__all__ = [
    "run_baseline",
    "evaluate_category",
    "judge",
    "CONFIG",
    "save_run",
    "security",
    "continuity",
    "reasoning",
    "tooling",
]
