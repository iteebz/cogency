"""Canonical evaluation configuration."""

import os
from pathlib import Path

from cogency import Agent


class Config:
    """Zero ceremony eval config."""

    def agent(self):
        """Create fresh agent per test."""
        return Agent(llm="gemini", mode="replay")

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
    use_llm_judge: bool = False  # Manual review for V3


CONFIG = Config()
