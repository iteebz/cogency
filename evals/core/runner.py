"""Evaluation execution engine - minimal runner facade."""

from .eval import Eval
from .notifications import callback as get_eval_notification_callback
from .suite import run_suite

__all__ = ["Eval", "run_suite", "get_eval_notification_callback"]
