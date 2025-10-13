from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.core.protocols import LLM
from cogency.lib.llms import Gemini, OpenAI


def test_protocol_compliance():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
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
    with patch("cogency.lib.rotation.get_api_key", return_value="factory-key"):
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
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
        providers = [OpenAI(), Gemini()]

        for provider in providers:
            # send() before connect() must fail
            with pytest.raises(RuntimeError, match="send\\(\\) requires active session"):
                async for _ in provider.send("test"):
                    pass

            # close() without session is safe no-op
            await provider.close()


def test_initial_session_state():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
        openai = OpenAI()
        gemini = Gemini()

        # OpenAI session state
        assert openai._connection is None
        assert openai._connection_manager is None

        # Gemini session state
        assert gemini._session is None
        assert gemini._connection is None


@pytest.mark.asyncio
async def test_http_methods_use_rotation():
    with patch("cogency.lib.rotation.get_api_key", return_value="base-key"):
        openai = OpenAI()

        # Test generate() uses rotation
        with patch("cogency.lib.llms.openai.with_rotation") as mock_rotation:
            mock_rotation.return_value = "mocked response"

            result = await openai.generate([{"role": "user", "content": "test"}])

            mock_rotation.assert_called_once()
            service, func = mock_rotation.call_args[0]
            assert service == "OPENAI"
            assert result == "mocked response"


@pytest.mark.asyncio
async def test_connect_forces_rotation():
    with patch("cogency.lib.rotation.get_api_key", return_value="base-key"):
        openai = OpenAI()

        with patch("cogency.lib.llms.openai.with_rotation") as mock_rotation:
            # Connection will fail, but rotation should be called
            mock_rotation.side_effect = RuntimeError("Mocked connection failure")

            with pytest.raises(RuntimeError, match="OpenAI connection failed"):
                await openai.connect([{"role": "user", "content": "test"}])

            # Verify rotation was called for fresh key
            mock_rotation.assert_called_once()
            service, func = mock_rotation.call_args[0]
            assert service == "OPENAI"
            assert callable(func)  # The function is a closure that wraps _create_client


def test_no_semantic_interpretation():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
        providers = [
            ("OpenAI", OpenAI()),
            ("Gemini", Gemini()),
        ]

        import inspect

        for name, provider in providers:
            # Check stream and send methods are pure pipes
            for method_name in ["stream", "send"]:
                method = getattr(provider, method_name)
                source = inspect.getsource(method)

                # Should NOT contain semantic markers
                assert "§execute" not in source, f"{name}.{method_name} contains §execute"
                assert "§end" not in source, f"{name}.{method_name} contains §end"


def test_native_chunking_only():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
        providers = [
            ("OpenAI", OpenAI()),
            ("Gemini", Gemini()),
        ]

        import inspect

        for name, provider in providers:
            for method_name in ["stream", "send"]:
                method = getattr(provider, method_name)
                source = inspect.getsource(method)

                # No character-level manipulation
                assert "char" not in source.lower(), f"{name}.{method_name} has char splitting"
                assert ".split(" not in source, f"{name}.{method_name} has string splitting"


def test_session_persistence_capability():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
        openai = OpenAI()
        gemini = Gemini()

        # Session state attributes exist for persistence
        assert hasattr(openai, "_connection")
        assert hasattr(openai, "_connection_manager")
        assert hasattr(gemini, "_session")
        assert hasattr(gemini, "_connection")


def test_fresh_key_rotation_architecture():
    with patch("cogency.lib.rotation.get_api_key", return_value="base-key"):
        openai = OpenAI()

        # Rotation integration exists
        import cogency.lib.llms.openai as openai_module

        assert hasattr(openai_module, "with_rotation")

        # connect() method has rotation call
        import inspect

        connect_source = inspect.getsource(openai.connect)
        assert "with_rotation" in connect_source
        assert "OPENAI" in connect_source


def test_provider_error_handling():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
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


def test_independent_instance_state():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key"):
        openai1 = OpenAI()
        openai2 = OpenAI()

        # Independent session state
        assert openai1._connection is None
        assert openai2._connection is None

        # Modifying one doesn't affect other
        openai1._connection = "session1"
        openai2._connection = "session2"

        assert openai1._connection != openai2._connection


@pytest.mark.asyncio
async def test_rotation_call_independence():
    with patch("cogency.lib.rotation.get_api_key", return_value="base-key"):
        openai = OpenAI()

        call_count = 0

        async def count_calls(service, func):
            nonlocal call_count
            call_count += 1
            # Mock client that will cause connection to fail cleanly
            from unittest.mock import Mock

            mock_client = Mock()
            mock_client.api_key = f"key-{call_count}"
            # Make beta.realtime.connect raise an error to avoid async context manager issues
            mock_client.beta.realtime.connect.side_effect = RuntimeError("Connection failed")
            return mock_client

        with patch("cogency.lib.llms.openai.with_rotation", side_effect=count_calls):
            # Each connect should trigger rotation
            for i in range(3):
                try:
                    session = await openai.connect([{"role": "user", "content": f"test {i}"}])
                    # Clean up the session if it was created
                    if hasattr(session, "close"):
                        await session.close()
                except RuntimeError:
                    pass  # Expected - connection will fail with mock

            # Should have called rotation 3 times
            assert call_count == 3
