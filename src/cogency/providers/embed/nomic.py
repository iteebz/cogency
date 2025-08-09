"""Nomic embedding provider - text vectorization with key rotation."""

import logging
from typing import Optional, Union

import numpy as np
from resilient_result import Err, Ok, Result

from .base import Embed

logger = logging.getLogger(__name__)


class NomicEmbed(Embed):
    """Nomic embedding provider with key rotation."""

    def __init__(
        self,
        api_keys: Union[str, list[str]] = None,
        model: str = "nomic-embed-text-v1.5",
        dimensionality: int = 768,
        batch_size: int = 3,
        task_type: str = "search_query",
        **kwargs,
    ):
        super().__init__(api_keys=api_keys, model=model, dimensionality=dimensionality, **kwargs)
        self._initialized = False
        self._batch_size = batch_size
        self._task_type = task_type

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
                raise ValueError("NOMIC_API_KEY required for NomicEmbed")

            try:
                import nomic

                nomic.login(self.api_key)
                self._initialized = True
                logger.info("Nomic API initialized")
            except ImportError:
                raise ImportError(
                    "nomic package required. Install with: pip install nomic"
                ) from None

    def embed(self, text: str | list[str], batch_size: Optional[int] = None, **kwargs) -> Result:
        """Embed text(s) - handles both single strings and lists."""
        if self._should_retry:
            from resilient_result import Retry, resilient

            @resilient(retry=Retry.api())
            def _resilient_embed():
                return self._embed_impl(text, batch_size, **kwargs)

            return _resilient_embed()
        return self._embed_impl(text, batch_size, **kwargs)

    def _embed_impl(
        self, text: str | list[str], batch_size: Optional[int] = None, **kwargs
    ) -> Result:
        """Internal embed implementation."""
        self._rotate_client()
        self._ensure_initialized()

        texts = [text] if isinstance(text, str) else text
        if not texts:
            return Ok([])

        # Use provided batch size or default
        bsz = batch_size or self._batch_size

        try:
            from nomic import embed

            # Process in batches if needed
            if len(texts) > bsz:
                logger.info(f"Processing {len(texts)} texts in batches of {bsz}")
                all_embeddings = []

                for i in range(0, len(texts), bsz):
                    batch = texts[i : i + bsz]
                    logger.debug(f"Processing batch {i // bsz + 1}/{(len(texts) + bsz - 1) // bsz}")

                    batch_result = embed.text(
                        texts=batch,
                        model=self.model,
                        dimensionality=self.dimensionality,
                        task_type=self._task_type,
                        **kwargs,
                    )
                    all_embeddings.extend(batch_result["embeddings"])

                logger.info(f"Successfully embedded {len(texts)} texts")
                return Ok([np.array(emb) for emb in all_embeddings])
            else:
                # Single batch
                result = embed.text(
                    texts=texts,
                    model=self.model,
                    dimensionality=self.dimensionality,
                    task_type=self._task_type,
                    **kwargs,
                )
                logger.info(f"Successfully embedded {len(texts)} texts")
                return Ok([np.array(emb) for emb in result["embeddings"]])

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")

            if "api" in str(e).lower() or "auth" in str(e).lower():
                logger.error("This might be an API key issue. Check your NOMIC_API_KEY.")

            return Err(e)

    def set_model(self, model: str, dims: int = 768):
        """
        Set the embedding model and dimensionality

        Args:
            model: Model name (e.g., 'nomic-embed-text-v2')
            dims: Embedding dimensions
        """
        self.model = model
        # Update base class dimensionality through property
        super().__init__(api_keys=self.keys.api_key, model=model, dimensionality=dims)
        logger.info(f"Model set to {model} with {dims} dimensions")
