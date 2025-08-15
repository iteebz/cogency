"""Base provider interface and router."""

from typing import List, Dict, Any

from . import anthropic, gemini, openai


PROVIDERS = {
    "openai": openai,
    "anthropic": anthropic,
    "gemini": gemini
}


async def generate(
    prompt: str = None, 
    messages: List[Dict] = None, 
    model: str = "gpt-4o-mini",
    provider: str = None
) -> str:
    """Generate response using specified provider."""
    
    # Auto-detect provider from model name if not specified
    if not provider:
        if model.startswith("gpt") or model.startswith("o1"):
            provider = "openai"
        elif model.startswith("claude"):
            provider = "anthropic"
        elif model.startswith("gemini"):
            provider = "gemini"
        else:
            provider = "openai"  # Default
    
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(PROVIDERS.keys())}")
    
    provider_module = PROVIDERS[provider]
    return await provider_module.generate(prompt=prompt, messages=messages, model=model)