"""Mistral provider - LLM and embedding with streaming, key rotation."""

from typing import AsyncIterator, Dict, List, Union

import numpy as np
from mistralai import Mistral as MistralClient
from resilient_result import Err, Ok, Result

from cogency.events import emit
from cogency.observe.tokens import cost, count

from .base import Provider


class Mistral(Provider):
    def __init__(
        self,
        llm_model: str = "mistral-small-latest",
        embed_model: str = "mistral-embed",
        dimensionality: int = 1024,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_p: float = 1.0,
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(model=llm_model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Mistral-specific params
        self.embed_model = embed_model
        self.dimensionality = dimensionality
        self.top_p = top_p

    def _get_client(self):
        return MistralClient(api_key=self.next_key())

    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
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
        emit(
            "provider",
            provider=self.provider_name,
            model=self.model,
            tin=tin,
            tout=tout,
            cost=cost(tin, tout, self.model),
        )

        # Cache response
        if self._cache:
            await self._cache.set(messages, response, cache_type="llm", **kwargs)

        return Ok(response)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate streaming LLM response."""
        client = self._get_client()
        stream = await client.chat.stream_async(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.data.choices[0].delta.content:
                yield chunk.data.choices[0].delta.content

    async def embed(self, text: Union[str, List[str]], **kwargs) -> Result:
        """Generate embeddings using Mistral embedding API."""
        # Check cache first
        if self._cache:
            cached_response = await self._cache.get(text, model=self.embed_model, **kwargs)
            if cached_response:
                return Ok(cached_response)

        try:
            client = self._get_client()
            inputs = [text] if isinstance(text, str) else text

            # Build API parameters
            api_kwargs = {
                "model": self.embed_model,
                "inputs": inputs,
            }

            # Add custom dimensionality if not default
            if self.dimensionality != 1024:
                api_kwargs["output_dimension"] = self.dimensionality

            response = await client.embeddings.create_async(**api_kwargs, **kwargs)
            result = [np.array(data.embedding) for data in response.data]

            # Cache result
            if self._cache:
                await self._cache.set(
                    text, result, cache_type="embed", model=self.embed_model, **kwargs
                )

            return Ok(result)

        except Exception as e:
            return Err(e)
