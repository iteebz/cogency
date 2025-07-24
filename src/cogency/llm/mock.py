from typing import AsyncGenerator

from cogency.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, response: str = "Mock response", api_keys=None, **kwargs):
        super().__init__(provider_name="mock", api_keys=api_keys or "mock_key", **kwargs)
        self.response = response

    async def _run_impl(self, messages, **kwargs) -> str:
        return self.response

    async def stream(self, messages, **kwargs) -> AsyncGenerator[str, None]:
        for char in self.response:
            yield char
