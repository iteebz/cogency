"""Test LLM - essential functionality only."""

import pytest

from cogency.services.llm import LLM
from tests.conftest import MockLLM


def test_abstract():
    with pytest.raises(TypeError):
        LLM("test-key")


@pytest.mark.asyncio
async def test_run():
    llm = MockLLM()
    messages = [{"role": "user", "content": "Hello"}]

    result = await llm.run(messages)
    assert result.success and result.data == "Mock response"


@pytest.mark.asyncio
async def test_stream():
    llm = MockLLM()
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    async for chunk in llm.stream(messages):
        chunks.append(chunk)
    assert len(chunks) >= 2


def test_key_rotation():
    keys = ["key1", "key2", "key3"]
    llm = MockLLM(api_keys=keys)

    key1 = llm.next_key()
    key2 = llm.next_key()
    assert key1 in keys
    assert key2 in keys

    llm_single = MockLLM(api_keys="single-key")
    assert llm_single.next_key() == "single-key"


def test_model():
    llm = MockLLM(model="custom-model")
    assert llm.model == "custom-model"
