# Base imports always available
from .base import BaseLLM
from .auto import detect_llm
from ..utils.keys import KeyManager, KeyRotator  # Unified key management

# Conditional imports for LLM providers
__all__ = ["BaseLLM", "detect_llm", "KeyManager", "KeyRotator"]

# OpenAI LLM
try:
    from .openai import OpenAILLM
    __all__.append("OpenAILLM")
except ImportError:
    pass

# Anthropic LLM
try:
    from .anthropic import AnthropicLLM
    __all__.append("AnthropicLLM")
except ImportError:
    pass

# Gemini LLM
try:
    from .gemini import GeminiLLM
    __all__.append("GeminiLLM")
except ImportError:
    pass

# Mistral LLM
try:
    from .mistral import MistralLLM
    __all__.append("MistralLLM")
except ImportError:
    pass

# Grok LLM (depends on OpenAI)
try:
    from .grok import GrokLLM
    __all__.append("GrokLLM")
except ImportError:
    pass