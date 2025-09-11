"""Canonical evaluation configuration."""

import os
import random

from cogency import Agent
from cogency.lib.storage import Paths


class Config:
    """Zero ceremony eval config."""

    def agent(self, llm=None, mode=None):
        """Create fresh agent per test."""
        return Agent(llm=llm or "gemini", mode=mode or self.mode, sandbox=True)

    @property
    def sample_size(self):
        return int(os.getenv("EVAL_SAMPLES", "30"))

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
        return int(os.getenv("EVAL_CONCURRENCY", "3"))

    @max_concurrent_tests.setter
    def max_concurrent_tests(self, value):
        os.environ["EVAL_CONCURRENCY"] = str(value)

    timeout: int = 15

    # Judging configuration
    judge_llm: str = (
        None  # None = raw output, "openai"/"anthropic" = cross-model judge (not same as agent)
    )

    # Transport mode for testing
    mode: str = "replay"  # replay, resume, auto

    # Security testing mode
    sandbox: bool = True  # Always sandbox for safety
    security_simulation: bool = True  # Simulate dangerous ops, don't execute


CONFIG = Config()
