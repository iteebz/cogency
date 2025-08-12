"""Provider mock fixtures for testing."""

from collections.abc import AsyncIterator
from typing import Union

import numpy as np
import pytest
from resilient_result import Err, Ok, Result

from cogency.providers import Provider
from cogency.providers.base import setup_rotator


# Base mock that can do both LLM and embedding
class MockProvider(Provider):
    """Mock provider for testing."""

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

        # Use canonical pattern
        rotator = setup_rotator("mock", api_keys, required=True)
        super().__init__(
            rotator=rotator,
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
            raise Exception("Mock provider failure")
        if self.custom_impl:
            return self.custom_impl(messages, **kwargs)
        return self.response

    async def _stream_impl(self, messages, **kwargs) -> AsyncIterator[str]:
        for char in self.response:
            yield char

    async def generate(self, messages: list[dict[str, str]], **kwargs) -> Result:
        """Mock generate method - canonical interface."""
        if self.should_fail:
            return Err(Exception("Mock provider failure"))
        if self.custom_impl:
            response = self.custom_impl(messages, **kwargs)
        else:
            response = self.response
        return Ok(response)

    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Mock stream method - yields realistic word chunks."""
        words = self.response.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " " + word
            else:
                yield word

    async def embed(self, text: Union[str, list[str]], **kwargs) -> Result:
        """Mock embed method - handles both string and list[str]."""
        if self.should_fail:
            return Err(Exception("Mock embed failure"))

        # Generate mock embeddings
        dimension = 384
        mock_embedding = [0.1, 0.2, 0.3] * (dimension // 3)

        if isinstance(text, str):
            return Ok([np.array(mock_embedding)])
        return Ok([np.array(mock_embedding) for _ in text])


def mock_provider(response: str, **kwargs):
    """Create a mock provider with specified response."""
    return MockProvider(response=response, **kwargs)


def mock_llm_factory(response: str = "Mock LLM response", **kwargs):
    """Create a mock LLM provider with specified response."""
    return MockLLM(response=response, **kwargs)


def mock_embed_factory(**kwargs):
    """Create a mock embedding provider."""
    return MockEmbed(**kwargs)


class RealisticMockProvider(Provider):
    """Mock provider with realistic response patterns for integration tests."""

    def __init__(self, responses: list[str] = None, **kwargs):
        self.responses = responses or [
            "I understand your request. Let me help you with that.",
            "Based on the information provided, here's my analysis:",
            "To accomplish this task, I'll need to use some tools.",
            "Here are the results of my investigation:",
            "I've completed the requested action successfully.",
        ]
        self.call_count = 0
        # Use canonical pattern
        rotator = setup_rotator("mock", "test", required=True)
        super().__init__(rotator=rotator, model="gpt-4-realistic-mock", **kwargs)

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

    async def run(self, messages: list[dict[str, str]], **kwargs) -> Result:
        """Realistic mock run method."""
        from resilient_result import Ok

        response = await self._run_impl(messages, **kwargs)
        return Ok(response)

    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Realistic mock stream method."""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk

    async def embed(self, text: Union[str, list[str]], **kwargs) -> Result:
        """Realistic mock embed method."""
        from resilient_result import Ok

        # Generate realistic mock embeddings
        dimension = 1536  # GPT-3 embedding dimension
        mock_embedding = [0.1, -0.2, 0.3] * (dimension // 3)

        if isinstance(text, str):
            return Ok([np.array(mock_embedding)])
        return Ok([np.array(mock_embedding) for _ in text])


# Specific aliases for clarity in tests
class MockLLM(MockProvider):
    """Mock LLM provider - same as MockProvider but clearer intent."""

    pass


class MockEmbed(MockProvider):
    """Mock embedding provider - same as MockProvider but clearer intent."""

    pass


@pytest.fixture
def mock_llm():
    """Mock LLM provider instance."""
    return MockLLM()


@pytest.fixture
def mock_embed():
    """Mock embedding provider instance."""
    return MockEmbed()


@pytest.fixture
def realistic_provider():
    """Realistic mock provider for integration tests."""
    return RealisticMockProvider()
