from .anthropic import Anthropic
from .gemini import Gemini
from .openai import OpenAI

__all__ = [
    "OpenAI",
    "Anthropic",
    "Gemini",
    "create",
]


def create(name: str):
    """Create LLM instance from string identifier."""
    factories = {
        "gemini": Gemini,
        "openai": OpenAI,
        "anthropic": Anthropic,
    }

    if name not in factories:
        valid = list(factories.keys())
        raise ValueError(f"Unknown LLM '{name}'. Valid options: {', '.join(valid)}")

    return factories[name]()
