"""Auto-detection of LLM providers from environment variables."""
from cogency.config import get_api_keys
from .base import BaseLLM

def auto_detect_llm() -> BaseLLM:
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
        from .grok import GrokLLM
        provider_map["grok"] = GrokLLM
    except ImportError:
        pass
    
    # Try Mistral
    try:
        from .mistral import MistralLLM
        provider_map["mistral"] = MistralLLM
    except ImportError:
        pass

    for provider_name, llm_class in provider_map.items():
        api_keys = get_api_keys(provider_name)
        if api_keys:
            return llm_class(api_keys=api_keys)

    # Clear error message with setup instructions
    available_providers = list(provider_map.keys())
    if not available_providers:
        raise RuntimeError(
            "No LLM providers installed. Install at least one:\n"
            "  - pip install cogency[openai]\n"
            "  - pip install cogency[anthropic]\n"
            "  - pip install cogency[gemini]\n"
            "  - pip install cogency[mistral]"
        )
    
    raise RuntimeError(
        f"No LLM provider configured. Available providers: {', '.join(available_providers)}\n"
        "Set an API key for one of the supported providers:\n"
        "  - OPENAI_API_KEY\n"
        "  - ANTHROPIC_API_KEY\n"
        "  - GEMINI_API_KEY\n"
        "  - GROK_API_KEY\n"
        "  - MISTRAL_API_KEY"
    )
