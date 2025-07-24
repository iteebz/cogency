from ..utils.auto import detect_embedder
from .base import BaseEmbed

__all__ = ["BaseEmbed", "detect_embedder"]

# OpenAI embeddings
try:
    from .openai import OpenAIEmbed

    __all__.append("OpenAIEmbed")
except ImportError:
    pass

# Nomic embeddings
try:
    from .nomic import NomicEmbed

    __all__.append("NomicEmbed")
except ImportError:
    pass

# Sentence Transformers embeddings
try:
    from .sentence import SentenceEmbed

    __all__.append("SentenceEmbed")
except ImportError:
    pass

# Mistral embeddings
try:
    from .mistral import MistralEmbed

    __all__.append("MistralEmbed")
except ImportError:
    pass
