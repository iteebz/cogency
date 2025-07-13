"""Auto-detection of LLM providers from environment variables."""
import os
from typing import Optional

from .anthropic import AnthropicLLM
from .base import BaseLLM
from .gemini import GeminiLLM
from .openai import OpenAILLM


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
    # Check for API keys in order of preference
    if openai_key := os.getenv("OPENAI_API_KEY"):
        return OpenAILLM(api_keys=openai_key)
    
    if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicLLM(api_keys=anthropic_key)
        
    if gemini_key := os.getenv("GEMINI_API_KEY"):
        return GeminiLLM(api_keys=gemini_key)
    
    # Clear error message with setup instructions
    raise RuntimeError(
        "No LLM provider configured. Set one of:\n"
        "  export OPENAI_API_KEY=your_key\n"
        "  export ANTHROPIC_API_KEY=your_key\n"
        "  export GEMINI_API_KEY=your_key"
    )