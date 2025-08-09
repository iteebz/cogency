"""Ollama provider - local LLM and embedding with OpenAI-compatible API."""

from typing import AsyncIterator, Dict, List, Union

import numpy as np
import openai
from resilient_result import Err, Ok, Result

from cogency.events import emit
from cogency.observe.tokens import cost, count

from .base import Provider


class Ollama(Provider):
    def __init__(
        self,
        llm_model: str = "llama3.1:8b",
        embed_model: str = "nomic-embed-text",
        dimensionality: int = 768,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        timeout: float = 60.0,  # Local models need more time
        base_url: str = "http://localhost:11434/v1",
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            **kwargs,
        )
        # Ollama-specific params
        self.embed_model = embed_model
        self.dimensionality = dimensionality
        self.base_url = base_url

    def _get_client(self):
        return openai.AsyncOpenAI(
            base_url=self.base_url,
            api_key="ollama",  # Ollama doesn't need real API key
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate LLM response with metrics and caching."""
        tin = count(messages, self.model)

        # Check cache first
        if self._cache:
            cached_response = await self._cache.get(messages, **kwargs)
            if cached_response:
                return Ok(cached_response)

        client = self._get_client()
        res = await client.chat.completions.create(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
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
        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._format(messages),
            stream=True,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: Union[str, List[str]], **kwargs) -> Result:
        """Generate embeddings using Ollama embedding API."""
        # Check cache first
        if self._cache:
            cached_response = await self._cache.get(text, model=self.embed_model, **kwargs)
            if cached_response:
                return Ok(cached_response)

        try:
            client = self._get_client()

            response = await client.embeddings.create(input=text, model=self.embed_model, **kwargs)

            if isinstance(text, str):
                result = [np.array(response.data[0].embedding)]
            else:
                result = [np.array(data.embedding) for data in response.data]

            # Cache result
            if self._cache:
                await self._cache.set(
                    text, result, cache_type="embed", model=self.embed_model, **kwargs
                )

            return Ok(result)

        except Exception as e:
            return Err(e)
