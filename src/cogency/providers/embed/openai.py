"""OpenAI embedding provider - text vectorization with key rotation."""

from typing import Union

import numpy as np
import openai
from resilient_result import Err, Ok, Result

from .base import Embed


class OpenAIEmbed(Embed):
    """OpenAI embedding provider with key rotation."""

    def __init__(
        self,
        api_keys: Union[str, list[str]] = None,
        model: str = "text-embedding-3-small",
        dimensionality: int = 1536,
        **kwargs,
    ):
        super().__init__(api_keys=api_keys, model=model, dimensionality=dimensionality, **kwargs)
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize OpenAI client with current key."""
        current_key = self.keys.current
        self._client = openai.OpenAI(api_key=current_key)

    def _get_client(self):
        """Get OpenAI client."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.key_rotator:
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
            # Build embedding parameters - clean, no ceremony
            api_kwargs = {
                "input": text,
                "model": self.model,
            }

            # Add dimensions for text-embedding-3 models
            if "text-embedding-3" in self.model:
                api_kwargs["dimensions"] = self.dimensionality

            response = self._client.embeddings.create(**api_kwargs, **kwargs)
            if isinstance(text, str):
                return Ok([np.array(response.data[0].embedding)])
            return Ok([np.array(data.embedding) for data in response.data])
        except Exception as e:
            return Err(e)
