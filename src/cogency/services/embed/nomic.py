import logging
from typing import Optional, Union

import numpy as np

from cogency.resilience import ConfigError
from cogency.utils.keys import KeyManager
from cogency.utils.results import Err, Ok, Result

from .base import BaseEmbed

logger = logging.getLogger(__name__)


class NomicEmbed(BaseEmbed):
    """Nomic embedding provider with key rotation."""

    def __init__(self, api_keys: Union[str, list[str]] = None, **kwargs):
        # Beautiful unified key management - auto-detects, handles all scenarios
        self.keys = KeyManager.for_provider("nomic", api_keys)
        super().__init__(self.keys.api_key, **kwargs)
        self._initialized = False
        self._model = "nomic-embed-text-v1.5"
        self._dimensionality = 768
        self._batch_size = 3

    def _init_client(self):
        """Initialize Nomic client with current key."""
        current_key = self.key_rotator.get_key() if self.key_rotator else self.api_key
        if current_key:
            try:
                import nomic

                nomic.login(current_key)
                self._initialized = True
                logger.info("Nomic API initialized")
            except ImportError:
                raise ImportError(
                    "nomic package required. Install with: pip install nomic"
                ) from None

    def _get_client(self):
        """Get client status."""
        return self._initialized

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.keys.has_multiple():
            self._init_client()

    def _ensure_initialized(self) -> None:
        """Initialize Nomic API connection if not already done"""
        if not self._initialized:
            if not self.api_key:
                raise ConfigError("NOMIC_API_KEY required for NomicEmbed", error_code="NO_API_KEY")

            try:
                import nomic

                nomic.login(self.api_key)
                self._initialized = True
                logger.info("Nomic API initialized")
            except ImportError:
                raise ImportError(
                    "nomic package required. Install with: pip install nomic"
                ) from None

    def embed_one(self, text: str, **kwargs) -> Result[np.ndarray, Exception]:
        """
        Embed a single text string

        Args:
            text: Text to embed
            **kwargs: Additional parameters for embedding

        Returns:
            Embedding vector as numpy array
        """
        result = self.embed_many([text], **kwargs)
        if result.failure:
            return Err(result.error)
        return Ok(result.data[0])

    def embed_many(
        self, texts: list[str], batch_size: Optional[int] = None, **kwargs
    ) -> Result[list[np.ndarray], Exception]:
        """
        Embed multiple texts with automatic batching

        Args:
            texts: List of texts to embed
            batch_size: Optional batch size override
            **kwargs: Additional parameters for embedding

        Returns:
            List of embedding vectors as numpy arrays
        """
        self._rotate_client()
        self._ensure_initialized()

        if not texts:
            return Ok([])

        # Use provided batch size or default
        bsz = batch_size or self._batch_size

        # Extract embedding parameters
        model = kwargs.get("model", self._model)
        dims = kwargs.get("dimensionality", self._dimensionality)

        try:
            from nomic import embed

            # Process in batches if needed
            if len(texts) > bsz:
                logger.info(f"Processing {len(texts)} texts in batches of {bsz}")
                all_embeddings = []

                for i in range(0, len(texts), bsz):
                    batch = texts[i : i + bsz]
                    logger.debug(f"Processing batch {i // bsz + 1}/{(len(texts) + bsz - 1) // bsz}")

                    batch_result = embed.text(texts=batch, model=model, dimensionality=dims)
                    all_embeddings.extend(batch_result["embeddings"])

                logger.info(f"Successfully embedded {len(texts)} texts")
                return Ok([np.array(emb) for emb in all_embeddings])
            else:
                # Single batch
                result = embed.text(texts=texts, model=model, dimensionality=dims)
                logger.info(f"Successfully embedded {len(texts)} texts")
                return Ok([np.array(emb) for emb in result["embeddings"]])

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")

            if "api" in str(e).lower() or "auth" in str(e).lower():
                logger.error("This might be an API key issue. Check your NOMIC_API_KEY.")

            return Err(e)

    @property
    def model(self) -> str:
        """Get the current embedding model"""
        return self._model

    @property
    def dimensionality(self) -> int:
        """Get the embedding dimensionality"""
        return self._dimensionality

    def set_model(self, model: str, dims: int = 768):
        """
        Set the embedding model and dimensionality

        Args:
            model: Model name (e.g., 'nomic-embed-text-v2')
            dims: Embedding dimensions
        """
        self._model = model
        self._dimensionality = dims
        logger.info(f"Model set to {model} with {dims} dimensions")
