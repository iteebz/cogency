"""Evaluation configuration."""

import os
import random

from cogency import Agent
from cogency.lib.paths import Paths


class Config:
    """Zero ceremony eval config."""

    def agent(self, llm=None, mode=None):
        """Create fresh agent per test."""
        return Agent(
            llm=llm or "gemini",
            mode=mode or self.mode,
            sandbox=True,
            max_iterations=self.max_iterations,
        )

    @property
    def sample_size(self):
        env_val = os.getenv("EVAL_SAMPLES")
        return int(env_val) if env_val else None

    @sample_size.setter
    def sample_size(self, value):
        os.environ["EVAL_SAMPLES"] = str(value)

    @property
    def seed(self):
        return int(os.getenv("EVAL_SEED", "42"))

    @seed.setter
    def seed(self, value):
        os.environ["EVAL_SEED"] = str(value)
        random.seed(value)  # Apply immediately

    @property
    def output_dir(self):
        return Paths.evals()

    @property
    def max_concurrent_tests(self):
        return getattr(self, "_max_concurrent_tests", 1)  # Default to 1

    @max_concurrent_tests.setter
    def max_concurrent_tests(self, value):
        self._max_concurrent_tests = value

    max_iterations: int = 3

    timeout: int = 60

    @property
    def judge(self):
        """Cross-model judge to prevent self-evaluation bias."""
        return getattr(self, "_judge", "gemini")  # Default to gemini judge
    
    @judge.setter
    def judge(self, value):
        self._judge = value

    # Transport mode for testing
    mode: str = "replay"  # replay, resume, auto

    # Security testing mode
    sandbox: bool = True  # Always sandbox for safety
    security_simulation: bool = True  # Simulate dangerous ops, don't execute


config = Config()
