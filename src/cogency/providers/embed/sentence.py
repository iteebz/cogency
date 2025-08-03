"""Sentence Transformers embedding provider - local text vectorization."""

import numpy as np
from resilient_result import Err, Ok, Result

from .base import Embed


class SentenceEmbed(Embed):
    """Sentence Transformers embedding provider - local, no API keys needed."""

    def __init__(self, model: str = "all-MiniLM-L6-v2", **kwargs):
        super().__init__(api_key=None, **kwargs)
        self._model = model
        self._model_instance = None
        self._init_model()

    def _init_model(self):
        """Initialize sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            self._model_instance = SentenceTransformer(self._model)
        except ImportError:
            raise ImportError(
                "Sentence Transformers support not installed. Use `pip install cogency[sentence]`"
            ) from None

    def embed(self, text: str | list[str], **kwargs) -> Result:
        """Embed text(s) - handles both single strings and lists."""
        if self._should_retry:
            from resilient_result import Retry, resilient

            @resilient(retry=Retry.api())
            def _resilient_embed():
                return self._embed_impl(text, **kwargs)

            return _resilient_embed()
        return self._embed_impl(text, **kwargs)

    def _embed_impl(self, text: str | list[str], **kwargs) -> Result:
        """Internal embed implementation."""
        try:
            embeddings = self._model_instance.encode(text, **kwargs)
            if isinstance(text, str):
                return Ok([np.array(embeddings)])
            return Ok([np.array(emb) for emb in embeddings])
        except Exception as e:
            return Err(e)

    @property
    def model(self) -> str:
        """Get the current embedding model."""
        return self._model

    @property
    def dimensionality(self) -> int:
        """Get embedding dimensionality."""
        if "MiniLM-L6" in self._model or "MiniLM-L12" in self._model:
            return 384
        elif "all-mpnet-base" in self._model:
            return 768
        else:
            return 384  # Default for MiniLM
