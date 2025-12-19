from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.core.protocols import LLM
from cogency.lib.llms import Gemini, OpenAI


def test_protocol_compliance():
    with (
        patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"),
        patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"),
    ):
        providers = [
            ("OpenAI", OpenAI()),
            ("Gemini", Gemini()),
        ]

        for name, provider in providers:
            assert isinstance(provider, LLM), f"{name} doesn't implement LLM protocol"

            methods = ["generate", "stream", "connect", "send", "close"]
            for method in methods:
                assert hasattr(provider, method), f"{name} missing {method}()"
                assert callable(getattr(provider, method)), f"{name}.{method} not callable"


def test_provider_factory_integration():
    with (
        patch("cogency.lib.llms.openai.get_api_key", return_value="factory-key"),
        patch("cogency.lib.llms.gemini.get_api_key", return_value="factory-key"),
    ):
        openai_agent = Agent(llm="openai")
        gemini_agent = Agent(llm="gemini")

        # Correct types
        assert isinstance(openai_agent.config.llm, OpenAI)
        assert isinstance(gemini_agent.config.llm, Gemini)


def test_invalid_provider_handling():
    with pytest.raises((ValueError, ImportError, KeyError)):
        Agent(llm="nonexistent_provider")


@pytest.mark.asyncio
async def test_session_state_requirements():
    with (
        patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"),
        patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"),
    ):
        providers = [OpenAI(), Gemini()]

        for provider in providers:
            # send() before connect() must fail
            try:
                aiterator = provider.send("test").__aiter__()
                await aiterator.__anext__()
                pytest.fail("RuntimeError was not raised when calling send() before connect()")
            except RuntimeError as e:
                assert "send() requires active session" in str(e)

            # close() without session is safe no-op
            await provider.close()


def test_provider_error_handling():
    with (
        patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"),
        patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"),
    ):
        providers = [
            ("OpenAI", OpenAI()),
            ("Gemini", Gemini()),
        ]

        import inspect

        for _name, provider in providers:
            # Check connect method has try/catch with logging
            connect_source = inspect.getsource(provider.connect)
            assert "try:" in connect_source
            assert "except" in connect_source
            assert "logger.warning" in connect_source
