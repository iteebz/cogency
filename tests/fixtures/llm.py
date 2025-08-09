"""LLM mock fixtures for testing."""

from typing import Any, AsyncIterator, List

import pytest
from resilient_result import Result

from cogency.providers.llm import LLM


class MockLLM(LLM):
    """Mock LLM for testing."""

    def __init__(
        self,
        response: str = "Mock response",
        should_fail: bool = False,
        api_keys: str = "mock_key",
        enable_cache: bool = False,
        model: str = "mock-model",
        custom_impl=None,
        **kwargs,
    ):
        self.response = response
        self.should_fail = should_fail
        self.custom_impl = custom_impl
        self._model = model
        super().__init__(
            provider_name="mock",
            api_keys=api_keys,
            enable_cache=enable_cache,
            model=model,
            **kwargs,
        )

    @property
    def default_model(self) -> str:
        """Default model for mock provider."""
        return "mock-model"

    def _get_client(self):
        """Get mock client instance."""
        return self  # Mock client is self

    async def _run_impl(self, messages, **kwargs) -> str:
        if self.should_fail:
            raise Exception("Mock LLM failure")
        if self.custom_impl:
            return self.custom_impl(messages, **kwargs)
        return self.response

    async def _stream_impl(self, messages, **kwargs) -> AsyncIterator[str]:
        for char in self.response:
            yield char


def mock_llm(response: str, **kwargs):
    """Create a mock LLM with specified response."""
    return MockLLM(response=response, **kwargs)


class RealisticMockLLM(LLM):
    """Mock LLM with realistic response patterns for integration tests."""

    def __init__(self, responses: List[str] = None, **kwargs):
        self.responses = responses or [
            "I understand your request. Let me help you with that.",
            "Based on the information provided, here's my analysis:",
            "To accomplish this task, I'll need to use some tools.",
            "Here are the results of my investigation:",
            "I've completed the requested action successfully.",
        ]
        self.call_count = 0
        super().__init__(api_keys="test", model="gpt-4-realistic-mock", **kwargs)

    @property
    def default_model(self) -> str:
        return "gpt-4-realistic-mock"

    def _get_client(self):
        return self

    async def _run_impl(self, messages, **kwargs) -> str:
        """Return realistic responses with tool calling patterns."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        # Simulate tool calling based on query content
        if len(messages) > 0:
            last_message = messages[-1].get("content", "").lower()
            if any(keyword in last_message for keyword in ["file", "search", "run", "execute"]):
                return f"{response}\n\nI should use a tool to help with this: shell(command='echo \"tool execution simulation\"')"

        return response

    async def _stream_impl(self, messages, **kwargs) -> AsyncIterator[str]:
        """Stream realistic response chunks."""
        response = await self._run_impl(messages, **kwargs)
        # Simulate streaming by yielding words
        words = response.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word


@pytest.fixture
def mock_llm():
    """Mock LLM instance."""
    return MockLLM()


@pytest.fixture
def realistic_llm():
    """Realistic mock LLM for integration tests."""
    return RealisticMockLLM()
