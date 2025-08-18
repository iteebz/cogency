"""Test core provider protocols."""

from typing import runtime_checkable

from cogency.lib.result import Ok


def test_llm_protocol_exists():
    """LLM protocol defined correctly."""
    from cogency.core.protocols import LLM

    assert hasattr(LLM, "generate")
    assert runtime_checkable(LLM)


def test_embedder_protocol_exists():
    """Embedder protocol defined correctly."""
    from cogency.core.protocols import Embedder

    assert hasattr(Embedder, "embed")
    assert runtime_checkable(Embedder)


def test_protocol_runtime_checking():
    """Protocols work with isinstance at runtime."""
    from cogency.core.protocols import LLM, Embedder

    class MockLLM:
        async def generate(self, messages):
            return Ok("response")

    class MockEmbedder:
        async def embed(self, texts):
            return Ok([[0.1, 0.2]])

    mock_llm = MockLLM()
    mock_embedder = MockEmbedder()

    assert isinstance(mock_llm, LLM)
    assert isinstance(mock_embedder, Embedder)
