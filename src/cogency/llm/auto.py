"""Auto-detection of LLM providers from environment variables."""
import os
from typing import Optional

from dotenv import load_dotenv

from .anthropic import AnthropicLLM
from .base import BaseLLM
from .gemini import GeminiLLM
from .grok import GrokLLM
from .mistral import MistralLLM
from .openai import OpenAILLM

# Auto-load .env file if it exists
load_dotenv()


def _detect_keys(prefix: str) -> Optional[list]:
    """Auto-detect API keys from environment with numbered fallback."""
    # Try numbered keys first (PREFIX_1, PREFIX_2, etc.)
    detected_keys = []
    for i in range(1, 10):  # Check 1-9
        key = os.getenv(f'{prefix}_{i}')
        if key:
            detected_keys.append(key)
    
    # Fall back to base key
    if not detected_keys:
        base_key = os.getenv(prefix)
        if base_key:
            detected_keys = [base_key]
    
    return detected_keys if detected_keys else None


def auto_detect_llm() -> BaseLLM:
    """Auto-detect LLM provider from environment variables.
    
    Fallback chain:
    1. Environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY)
    2. Config file (future)
    3. Clear error message
    
    Returns:
        BaseLLM: Configured LLM instance
        
    Raises:
        RuntimeError: If no API keys found
    """
    # Check for API keys in order of preference - auto-detect numbered keys
    if openai_keys := _detect_keys("OPENAI_API_KEY"):
        return OpenAILLM(api_keys=openai_keys)
    
    if anthropic_keys := _detect_keys("ANTHROPIC_API_KEY"):
        return AnthropicLLM(api_keys=anthropic_keys)
        
    if gemini_keys := _detect_keys("GEMINI_API_KEY"):
        return GeminiLLM(api_keys=gemini_keys)
    
    if grok_keys := _detect_keys("GROK_API_KEY"):
        return GrokLLM(api_keys=grok_keys)
    
    if mistral_keys := _detect_keys("MISTRAL_API_KEY"):
        return MistralLLM(api_keys=mistral_keys)
    
    # Clear error message with setup instructions
    raise RuntimeError(
        "No LLM provider configured. Set one of:\n"
        "  export OPENAI_API_KEY=your_key\n"
        "  export ANTHROPIC_API_KEY=your_key\n"
        "  export GEMINI_API_KEY=your_key\n"
        "  export GROK_API_KEY=your_key\n"
        "  export MISTRAL_API_KEY=your_key"
    )