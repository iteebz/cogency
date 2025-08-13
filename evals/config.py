"""Evaluation system configuration."""

from pathlib import Path

from cogency.providers.gemini import Gemini
from cogency.providers.openai import OpenAI

# Load evals/.env if it exists
try:
    from dotenv import load_dotenv

    evals_env = Path(__file__).parent / ".env"
    if evals_env.exists():
        load_dotenv(evals_env)
except ImportError:
    pass

# Evaluation Configuration
EVAL_CONFIG = {
    # Agent configuration - Gemini 2.5 Flash Lite (fast + cheap)
    "agent_provider": "gemini",
    "agent_model": "gemini-2.5-flash-lite",
    # Judge configuration - Different Gemini model for validation
    "judge_provider": "gemini",
    "judge_model": "gemini-2.0-flash-thinking",
    # Evaluation settings
    "max_iterations": 15,
    "timeout": 300,
    "concurrent_evals": 1,
    # Statistical requirements from evals.md
    "sample_sizes": {
        "security": 50,  # Injection resistance (50+ for trends)
        "tools": 100,  # Tool integration (100+ for regression detection)
        "reasoning": 100,  # Logic and problem-solving
        "memory": 30,  # Cross-session (expensive but critical)
        "network": 50,  # Network resilience
        "error_handling": 20,  # Edge cases (20+ minimum)
        "concurrency": 20,  # Concurrent operations
        "workflows": 50,  # Multi-step task completion
    },
}

# Provider mapping
PROVIDERS = {
    "gemini": Gemini,
    "openai": OpenAI,
}


def get_agent_provider():
    """Get agent provider instance."""
    provider_name = EVAL_CONFIG["agent_provider"]
    model = EVAL_CONFIG["agent_model"]

    if provider_name == "gemini":
        return Gemini(llm_model=model)
    if provider_name == "openai":
        return OpenAI(model=model)
    raise ValueError(f"Unsupported agent provider: {provider_name}")


def get_judge_provider():
    """Get judge provider instance."""
    provider_name = EVAL_CONFIG["judge_provider"]
    model = EVAL_CONFIG["judge_model"]

    if provider_name == "gemini":
        return Gemini(llm_model=model)
    if provider_name == "openai":
        return OpenAI(model=model)
    raise ValueError(f"Unsupported judge provider: {provider_name}")


def get_agent_model():
    """Get configured agent model."""
    return EVAL_CONFIG["agent_model"]


def get_judge_model():
    """Get configured judge model."""
    return EVAL_CONFIG["judge_model"]


def get_sample_size(category: str) -> int:
    """Get required sample size for evaluation category."""
    return EVAL_CONFIG["sample_sizes"].get(category, 50)  # Default 50


def get_max_iterations() -> int:
    """Get configured max iterations."""
    return EVAL_CONFIG["max_iterations"]


def get_timeout() -> int:
    """Get configured timeout."""
    return EVAL_CONFIG["timeout"]
