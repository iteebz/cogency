"""Canonical evaluation configuration."""

import os
from pathlib import Path

from cogency import Agent


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
    def output_dir(self):
        return Path.home() / ".cogency/evals"

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
