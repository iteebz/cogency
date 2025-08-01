"""Cogency evaluation framework - minimal, fast, beautiful."""

from .base import Eval, EvalResult
from .runner import run_eval, run_suite

__all__ = ["Eval", "EvalResult", "run_eval", "run_suite"]
