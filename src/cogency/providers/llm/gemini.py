"""Google Gemini provider - streaming chat with tool calling and key rotation."""

from typing import AsyncIterator, Dict, List

import google.genai as genai

from cogency.providers.llm.base import LLM


class Gemini(LLM):
    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_k: int = 40,
        top_p: float = 1.0,
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Gemini-specific params
        self.top_k = top_k
        self.top_p = top_p

    def _get_client(self):
        return genai.Client(api_key=self.next_key())

    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        client = self._get_client()

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
        return response.text

    async def _stream_impl(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        client = self._get_client()

        try:
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
        except Exception as e:
            raise e
