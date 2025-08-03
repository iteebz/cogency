"""Mistral embedding provider - text vectorization with key rotation."""

from typing import Union

import numpy as np
from mistralai import Mistral
from resilient_result import Err, Ok, Result

from cogency.utils.keys import KeyManager

from .base import Embed


class MistralEmbed(Embed):
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
        current_key = self.keys.current
        if not current_key:
            raise ValueError("API key must be provided either directly or via KeyRotator")
        self._client = Mistral(api_key=current_key)

    def _get_client(self):
        """Get Mistral client."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.keys.has_multiple():
            self._init_client()

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
            self._rotate_client()
            inputs = [text] if isinstance(text, str) else text
            response = self._client.embeddings.create(model=self._model, inputs=inputs, **kwargs)
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
