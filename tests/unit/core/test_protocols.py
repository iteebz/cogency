"""Test core provider protocols."""

from typing import runtime_checkable

from cogency.lib.result import Ok


def test_llm_protocol_exists():
    """LLM protocol defined correctly."""
    from cogency.core.protocols import LLM

    assert hasattr(LLM, "generate")
    assert runtime_checkable(LLM)


def test_protocol_runtime_checking():
    """Protocols work with isinstance at runtime."""
    from cogency.core.protocols import LLM

    class MockLLM:
        async def generate(self, messages):
            return Ok("response")

    mock_llm = MockLLM()
    assert isinstance(mock_llm, LLM)
