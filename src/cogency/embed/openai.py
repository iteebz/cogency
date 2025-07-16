import os
from typing import List, Optional, Union

import numpy as np

try:
    import openai
except ImportError:
    raise ImportError("OpenAI support not installed. Use `pip install cogency[openai]`")

from cogency.llm.key_rotator import KeyRotator
from cogency.utils.errors import ConfigurationError

from .base import BaseEmbed


class OpenAIEmbed(BaseEmbed):
    """OpenAI embedding provider with key rotation."""

    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "text-embedding-3-small",
        **kwargs,
    ):
        # Auto-detect API keys from environment if not provided
        if api_keys is None:
            # Try numbered keys first (OPENAI_API_KEY_1, etc.)
            detected_keys = []
            for i in range(1, 10):  # Check 1-9
                key = os.getenv(f'OPENAI_API_KEY_{i}')
                if key:
                    detected_keys.append(key)
            
            # Fall back to base OPENAI_API_KEY
            if not detected_keys:
                base_key = os.getenv('OPENAI_API_KEY')
                if base_key:
                    detected_keys = [base_key]
                    
            if detected_keys:
                api_keys = detected_keys
            else:
                raise ConfigurationError("API keys must be provided", error_code="NO_API_KEYS")

        # Handle key rotation
        if isinstance(api_keys, list) and len(api_keys) > 1:
            self.key_rotator = KeyRotator(api_keys)
            api_key = None
        elif isinstance(api_keys, list) and len(api_keys) == 1:
            self.key_rotator = None
            api_key = api_keys[0]
        else:
            self.key_rotator = None
            api_key = api_keys

        super().__init__(api_key, **kwargs)
        self.model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize OpenAI client with current key."""
        current_key = self.key_rotator.get_key() if self.key_rotator else self.api_key
        self._client = openai.OpenAI(api_key=current_key)

    def _get_client(self):
        """Get OpenAI client."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.key_rotator:
            self._init_client()

    def embed_single(self, text: str, **kwargs) -> np.ndarray:
        """Embed a single text string."""
        self._rotate_client()
        response = self._client.embeddings.create(
            input=text,
            model=self.model,
            **kwargs
        )
        return np.array(response.data[0].embedding)

    def embed_batch(self, texts: List[str], **kwargs) -> List[np.ndarray]:
        """Embed multiple texts."""
        self._rotate_client()
        response = self._client.embeddings.create(
            input=texts,
            model=self.model,
            **kwargs
        )
        return [np.array(data.embedding) for data in response.data]

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
