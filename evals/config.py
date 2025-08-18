"""Evaluation configuration - single source of truth."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from cogency import Agent


@dataclass
class EvalConfig:
    """Zero ceremony evaluation configuration."""
    agent: Callable = lambda: Agent()
    
    # Judge configuration
    judge_llm: str = "openai"       # "openai", "claude", "gemini", or provider instance
    use_llm_judge: bool = False     # Start with raw review, add judge later
    
    # Statistical rigor
    sample_size: int = 20  # Full test coverage per category  
    num_runs: int = 1  # For initial baseline, scale to 3-5 for significance
    random_seed: int = 42
    
    # Output control
    output_dir: Path = Path("evals/runs")
    save_raw_outputs: bool = True  # For manual review
    
    # Sampling strategy  
    stratified_sampling: bool = True   # Balance difficulty across samples
    temporal_sampling: bool = False    # Future: avoid recency bias


CONFIG = EvalConfig()