"""Auto-detection of LLM providers from environment variables."""
from cogency.config import get_api_keys
from .base import BaseLLM
from .openai import OpenAILLM
from .anthropic import AnthropicLLM
from .gemini import GeminiLLM
from .grok import GrokLLM
from .mistral import MistralLLM

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
    provider_map = {
        "openai": OpenAILLM,
        "anthropic": AnthropicLLM,
        "gemini": GeminiLLM,
        "grok": GrokLLM,
        "mistral": MistralLLM,
    }

    for provider_name, llm_class in provider_map.items():
        api_keys = get_api_keys(provider_name)
        if api_keys:
            return llm_class(api_keys=api_keys)

    # Clear error message with setup instructions
    raise RuntimeError(
        "No LLM provider configured. Set an API key for one of the supported providers:\n"
        "  - OPENAI_API_KEY\n"
        "  - ANTHROPIC_API_KEY\n"
        "  - GEMINI_API_KEY\n"
        "  - GROK_API_KEY\n"
        "  - MISTRAL_API_KEY"
    )
