# Base imports always available
from .base import BaseLLM
from .auto import auto_detect_llm
from .key_rotator import KeyRotator

# Conditional imports for LLM providers
__all__ = ["BaseLLM", "auto_detect_llm", "KeyRotator"]

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