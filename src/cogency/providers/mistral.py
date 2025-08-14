"""Mistral provider - LLM and embedding with streaming, key rotation."""

from collections.abc import AsyncIterator
from typing import Union

import numpy as np
from mistralai import Mistral as MistralClient
from resilient_result import Err, Ok, Result


try:
    from .tokens import cost, count

    from .base import Provider, rotate_retry, setup_rotator
except ImportError:
    from tokens import cost, count
    from base import Provider, rotate_retry, setup_rotator


class Mistral(Provider):
    def __init__(
        self,
        api_keys=None,
        llm_model: str = "mistral-small-latest",
        embed_model: str = "mistral-embed",
        dimensionality: int = 1024,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_p: float = 1.0,
        **kwargs,
    ):
        rotator = setup_rotator("mistral", api_keys, required=True)

        super().__init__(
            rotator=rotator,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        # Mistral-specific params
        self.embed_model = embed_model
        self.dimensionality = dimensionality
        self.top_p = top_p

    def _get_client(self):
        return MistralClient(api_key=self.next_key())

    @rotate_retry
    async def generate(self, messages: list[dict[str, str]], **kwargs) -> Result:
        """Generate LLM response with metrics and caching."""
        tin = count(messages, self.model)

        # Check cache first
        if self._cache:
            cached_response = await self._cache.get(messages, **kwargs)
            if cached_response:
                return Ok(cached_response)

        client = self._get_client()
        res = await client.chat.complete_async(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            **kwargs,
        )
        response = res.choices[0].message.content

        tout = count([{"role": "assistant", "content": response}], self.model)
