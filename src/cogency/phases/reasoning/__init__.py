"""Enhanced cognitive reasoning subsystem."""

from .prompt import prompt_reasoning
from .switching import parse_switch, should_switch, switch_mode

__all__ = [
    "parse_switch",
    "should_switch",
    "switch_mode",
    "prompt_reasoning",
]
