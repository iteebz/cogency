"""Google Gemini provider - LLM and embedding with streaming, key rotation."""

from typing import AsyncIterator, Dict, List, Union

import google.genai as genai
import numpy as np
from resilient_result import Err, Ok, Result

from cogency.events import emit
from cogency.observe.tokens import cost, count

from .base import Provider


class Gemini(Provider):
    def __init__(
        self,
        llm_model: str = "gemini-2.0-flash-exp",
        embed_model: str = "gemini-embedding-001",
        dimensionality: int = 768,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_k: int = 40,
        top_p: float = 1.0,
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(model=llm_model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Gemini-specific params
        self.embed_model = embed_model
        self.dimensionality = dimensionality
        self.top_k = top_k
        self.top_p = top_p

    def _get_client(self):
        return genai.Client(api_key=self.next_key())

    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate LLM response with metrics and caching."""
        tin = count(messages, self.model)

        # Check cache first
        if self._cache:
            cached_response = await self._cache.get(messages, **kwargs)
            if cached_response:
                return Ok(cached_response)

        client = self._get_client()
        formatted_messages = self._format(messages)
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in formatted_messages])

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_k=self.top_k,
                top_p=self.top_p,
                **{k: v for k, v in kwargs.items() if k in ["stop_sequences"]},
            ),
        )
        response_text = response.text

        tout = count([{"role": "assistant", "content": response_text}], self.model)
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
            await self._cache.set(messages, response_text, cache_type="llm", **kwargs)

        return Ok(response_text)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate streaming LLM response."""
        client = self._get_client()
        formatted_messages = self._format(messages)
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in formatted_messages])

        async for chunk in await client.aio.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_k=self.top_k,
                top_p=self.top_p,
                **{k: v for k, v in kwargs.items() if k in ["stop_sequences"]},
            ),
        ):
            if chunk.text:
                yield chunk.text

    async def embed(self, text: Union[str, List[str]], **kwargs) -> Result:
        """Generate embeddings using Gemini embedding API."""
        # Check cache first
        if self._cache:
            cached_response = await self._cache.get(text, model=self.embed_model, **kwargs)
            if cached_response:
                return Ok(cached_response)

        try:
            client = self._get_client()
            inputs = [text] if isinstance(text, str) else text

            config = genai.types.EmbedContentConfig(output_dimensionality=self.dimensionality)
            response = await client.aio.models.embed_content(
                model=self.embed_model,
                contents=inputs,
                config=config,
                **kwargs,
            )
            embeddings = [np.array(emb.values) for emb in response.embeddings]

            # Cache result
            if self._cache:
                await self._cache.set(
                    text, embeddings, cache_type="embed", model=self.embed_model, **kwargs
                )

            return Ok(embeddings)

        except Exception as e:
            return Err(e)
