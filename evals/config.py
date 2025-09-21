"""Evaluation configuration."""

import random

from cogency import Agent
from cogency.lib.paths import Paths


class Config:
    """Zero ceremony eval config."""

    sample_size: int = 2
    seed: int = 42
    max_iterations: int = 3
    timeout: int = 60
    max_concurrent_tests: int = 2
    mode: str = "replay"  # replay, resume, auto
    llm: str = "gemini"  # Default LLM
    sandbox: bool = True  # Always sandbox for safety
    security_simulation: bool = True  # Simulate dangerous ops, don't execute

    def __init__(self):
        self._judge = "gemini"
        random.seed(self.seed)

    def agent(self, llm=None, mode=None, **kwargs):
        """Create fresh agent per test."""
        return Agent(
            llm=llm or "gemini",
            mode=mode or self.mode,
            sandbox=True,
            max_iterations=self.max_iterations,
            profile=kwargs.pop("profile", False),  # Default off for evals
            **kwargs,  # Direct parameter pass-through
        )

    @property
    def output_dir(self):
        return Paths.evals()

    @property
    def judge(self):
        """Cross-model judge to prevent self-evaluation bias."""
        return self._judge

    @judge.setter
    def judge(self, value):
        self._judge = value


config = Config()
