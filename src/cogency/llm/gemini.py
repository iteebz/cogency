import asyncio
from typing import AsyncIterator, Dict, List, Union

try:
    from google import genai
except ImportError:
    raise ImportError(
        "Google Gemini support not installed. Use `pip install google-genai`"
    ) from None

from cogency.llm.base import BaseLLM
from cogency.resilience import safe


class GeminiLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "gemini-2.5-flash",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_retries: int = 3,
        **kwargs,
    ):
        super().__init__("gemini", api_keys)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries

        # Build kwargs for Gemini client
        self.kwargs = {
            "timeout": timeout,
            "temperature": temperature,
            "max_retries": max_retries,
            **kwargs,
        }

        self._clients: Dict[str, genai.Client] = {}  # Cache for client instances

    def _get_client(self):
        """Get client instance with current API key."""
        current_key = self.next_key()

        if current_key not in self._clients:
            self._clients[current_key] = genai.Client(api_key=current_key)

        return self._clients[current_key]

    @safe()
    async def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        client = self._get_client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=self.temperature,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k in ["max_output_tokens", "top_p", "top_k", "stop_sequences"]
                },
            ),
        )

        return response.text

    @safe()
    async def stream(
        self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs
    ) -> AsyncIterator[str]:
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        client = self._get_client()
        async for chunk in await client.aio.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=self.temperature,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k in ["max_output_tokens", "top_p", "top_k", "stop_sequences"]
                },
            ),
        ):
            if chunk.text:
                yield chunk.text
                if yield_interval > 0:
                    await asyncio.sleep(yield_interval)
