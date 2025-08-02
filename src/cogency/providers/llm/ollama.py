"""Ollama provider - local models with OpenAI-compatible API."""

from typing import AsyncIterator, Dict, List

import openai

from cogency.providers.llm.base import LLM


class Ollama(LLM):
    def __init__(self, base_url: str = "http://localhost:11434/v1", **kwargs):
        self.base_url = base_url
        super().__init__("ollama", **kwargs)

    @property
    def default_model(self) -> str:
        return "llama2"  # Popular local model default

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
            self._handle_error(e)
