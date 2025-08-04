"""Token counting and cost estimation - emits token events."""

from typing import Dict, List

import tiktoken

# Current pricing ($/1K tokens) - updated Jan 2025
COSTS = {
    # OpenAI
    "gpt-4o": {"in": 0.0025, "out": 0.01},
    "gpt-4o-mini": {"in": 0.00015, "out": 0.0006},
    "gpt-4-turbo": {"in": 0.01, "out": 0.03},
    "gpt-3.5-turbo": {"in": 0.0005, "out": 0.0015},
    # Anthropic
    "claude-3-5-sonnet-20241022": {"in": 0.003, "out": 0.015},
    "claude-3-5-haiku-20241022": {"in": 0.0008, "out": 0.004},
    "claude-3-opus-20240229": {"in": 0.015, "out": 0.075},
    # Mistral
    "mistral-large-latest": {"in": 0.002, "out": 0.006},
    "mistral-small-latest": {"in": 0.0002, "out": 0.0006},
    # Fallback
    "default": {"in": 0.001, "out": 0.003},
}


def count(msgs: List[Dict[str, str]], model: str = "gpt-4o") -> int:
    """Count tokens in messages."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    total = 0
    for msg in msgs:
        total += len(enc.encode(msg.get("content", "")))
        total += 4  # Role tokens
    total += 2  # Chat format overhead

    # Emit token count event
    from cogency.events import emit

    emit("token_count", level="debug", model=model, count=total, messages=len(msgs))

    return total


def cost(tin: int, tout: int, model: str) -> float:
    """Estimate cost in USD."""
    rates = COSTS.get(model, COSTS["default"])
    cost_usd = (tin * rates["in"] + tout * rates["out"]) / 1000

    # Emit cost event
    from cogency.events import emit

    emit("token_cost", level="debug", model=model, tin=tin, tout=tout, cost=cost_usd)

    return cost_usd
