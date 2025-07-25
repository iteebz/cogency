from typing import Union

import numpy as np

from cogency.utils.results import Err, Ok, Result

try:
    import openai
except ImportError:
    raise ImportError("OpenAI support not installed. Use `pip install cogency[openai]`") from None

from cogency.utils.keys import KeyManager

from .base import BaseEmbed


class OpenAIEmbed(BaseEmbed):
    """OpenAI embedding provider with key rotation."""

    def __init__(
        self,
        api_keys: Union[str, list[str]] = None,
        model: str = "text-embedding-3-small",
        **kwargs,
    ):
        # Beautiful unified key management - auto-detects, handles all scenarios
        self.keys = KeyManager.for_provider("openai", api_keys)
        super().__init__(self.keys.api_key, **kwargs)
        self.model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize OpenAI client with current key."""
        current_key = self.keys.get_current()
        self._client = openai.OpenAI(api_key=current_key)

    def _get_client(self):
        """Get OpenAI client."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.key_rotator:
            self._init_client()

    def embed_one(self, text: str, **kwargs) -> Result[np.ndarray, Exception]:
        """Embed a single text string."""
        try:
            self._rotate_client()
            response = self._client.embeddings.create(input=text, model=self.model, **kwargs)
            return Ok(np.array(response.data[0].embedding))
        except Exception as e:
            return Err(e)

    def embed_many(self, texts: list[str], **kwargs) -> Result[list[np.ndarray], Exception]:
        """Embed multiple texts."""
        try:
            self._rotate_client()
            response = self._client.embeddings.create(input=texts, model=self.model, **kwargs)
            return Ok([np.array(data.embedding) for data in response.data])
        except Exception as e:
            return Err(e)

    @property
    def dimensionality(self) -> int:
        """Get embedding dimensionality."""
        if "3-small" in self.model:
            return 1536
        elif "3-large" in self.model:
            return 3072
        elif "ada-002" in self.model:
            return 1536
        else:
            return 1536  # Default
