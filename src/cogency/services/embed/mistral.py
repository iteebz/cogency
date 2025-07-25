from typing import Union

import numpy as np

from cogency.utils.results import Err, Ok, Result

try:
    from mistralai import Mistral
except ImportError:
    raise ImportError("Mistral support not installed. Use `pip install cogency[mistral]`") from None

from cogency.resilience import ConfigError
from cogency.utils.keys import KeyManager

from .base import BaseEmbed


class MistralEmbed(BaseEmbed):
    """Mistral embedding provider with key rotation."""

    def __init__(
        self,
        api_keys: Union[str, list[str]] = None,
        model: str = "mistral-embed",
        **kwargs,
    ):
        # Beautiful unified key management - auto-detects, handles all scenarios
        self.keys = KeyManager.for_provider("mistral", api_keys)
        super().__init__(self.keys.api_key, **kwargs)
        self._model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize Mistral client with current key."""
        current_key = self.keys.get_current()
        if not current_key:
            raise ConfigError(
                "API key must be provided either directly or via KeyRotator.",
                error_code="NO_CURRENT_API_KEY",
            )
        self._client = Mistral(api_key=current_key)

    def _get_client(self):
        """Get Mistral client."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.keys.has_multiple():
            self._init_client()

    def embed_one(self, text: str, **kwargs) -> Result[np.ndarray, Exception]:
        """Embed a single text string."""
        try:
            self._rotate_client()
            response = self._client.embeddings.create(model=self._model, inputs=[text], **kwargs)
            return Ok(np.array(response.data[0].embedding))
        except Exception as e:
            return Err(e)

    def embed_many(self, texts: list[str], **kwargs) -> Result[list[np.ndarray], Exception]:
        """Embed multiple texts."""
        try:
            self._rotate_client()
            response = self._client.embeddings.create(model=self._model, inputs=texts, **kwargs)
            return Ok([np.array(data.embedding) for data in response.data])
        except Exception as e:
            return Err(e)

    @property
    def model(self) -> str:
        """Get the current embedding model."""
        return self._model

    @property
    def dimensionality(self) -> int:
        """Get embedding dimensionality."""
        return 1024  # mistral-embed outputs 1024-dimensional vectors
