"""Auto-detection of LLM providers from environment variables."""
from cogency.utils.auto import detect_provider
from .base import BaseLLM

def detect_llm() -> BaseLLM:
    """Auto-detect LLM provider from environment variables.
    
    Fallback chain:
    1. OpenAI
    2. Anthropic
    3. Gemini
    4. Grok
    5. Mistral
    
    Returns:
        BaseLLM: Configured LLM instance
        
    Raises:
        RuntimeError: If no API keys found for any provider.
    """
    # Build provider map dynamically based on available imports
    provider_map = {}
    
    # Try OpenAI
    try:
        from .openai import OpenAILLM
        provider_map["openai"] = OpenAILLM
    except ImportError:
        pass
    
    # Try Anthropic
    try:
        from .anthropic import AnthropicLLM
        provider_map["anthropic"] = AnthropicLLM
    except ImportError:
        pass
    
    # Try Gemini
    try:
        from .gemini import GeminiLLM
        provider_map["gemini"] = GeminiLLM
    except ImportError:
        pass
    
    # Try Grok
    try:
        from .xai import GrokLLM
        provider_map["grok"] = GrokLLM
    except ImportError:
        pass
    
    # Try Mistral
    try:
        from .mistral import MistralLLM
        provider_map["mistral"] = MistralLLM
    except ImportError:
        pass

    return detect_provider(provider_map, "LLM")
