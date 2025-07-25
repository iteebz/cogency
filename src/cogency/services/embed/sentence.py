import numpy as np

from cogency.utils.results import Err, Ok, Result

from .base import BaseEmbed


class SentenceEmbed(BaseEmbed):
    """Sentence Transformers embedding provider - local, no API keys needed."""

    def __init__(self, model: str = "all-MiniLM-L6-v2", **kwargs):
        super().__init__(api_key=None, **kwargs)
        self.model = model
        self._model_instance = None
        self._init_model()

    def _init_model(self):
        """Initialize sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            self._model_instance = SentenceTransformer(self.model)
        except ImportError:
            raise ImportError(
                "Sentence Transformers support not installed. "
                "Use `pip install cogency[sentence-transformers]`"
            ) from None

    def embed_one(self, text: str, **kwargs) -> Result[np.ndarray, Exception]:
        """Embed a single text string."""
        try:
            return Ok(self._model_instance.encode(text, **kwargs))
        except Exception as e:
            return Err(e)

    def embed_many(self, texts: list[str], **kwargs) -> Result[list[np.ndarray], Exception]:
        """Embed multiple texts."""
        try:
            embeddings = self._model_instance.encode(texts, **kwargs)
            return Ok([np.array(emb) for emb in embeddings])
        except Exception as e:
            return Err(e)

    @property
    def dimensionality(self) -> int:
        """Get embedding dimensionality."""
        if "MiniLM-L6" in self.model or "MiniLM-L12" in self.model:
            return 384
        elif "all-mpnet-base" in self.model:
            return 768
        else:
            return 384  # Default for MiniLM
