"""Ollama provider - local models with OpenAI-compatible API."""

from typing import AsyncIterator, Dict, List

import openai

from cogency.providers.llm.base import LLM


class Ollama(LLM):
    def __init__(
        self,
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        timeout: float = 60.0,  # Local models need more time
        base_url: str = "http://localhost:11434/v1",
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(
            model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout, **kwargs
        )
        # Ollama-specific params
        self.base_url = base_url

    def _get_client(self):
        return openai.AsyncOpenAI(
            base_url=self.base_url,
            api_key="ollama",  # Ollama doesn't need real API key
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        res = await client.chat.completions.create(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )
        return res.choices[0].message.content

    async def _stream_impl(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        try:
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
        except Exception as e:
            raise e
