"""Tests for GeminiLLM implementation."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.llm.gemini import GeminiLLM
from cogency.llm.key_rotator import KeyRotator
from cogency.utils.errors import ConfigurationError


class TestGeminiLLM:
    """Test suite for GeminiLLM."""

    def test_initialization_single_key(self):
        """Test GeminiLLM initialization with single API key."""
        llm = GeminiLLM(api_keys="test-key")

        assert llm.api_key == "test-key"
        assert llm.key_rotator is None
        assert llm.model == "gemini-2.5-flash"
        assert llm.timeout == 15.0
        assert llm.temperature == 0.7

    def test_initialization_single_key_list(self):
        """Test GeminiLLM initialization with single key in list."""
        llm = GeminiLLM(api_keys=["test-key"])

        assert llm.api_key == "test-key"
        assert llm.key_rotator is None

    def test_initialization_multiple_keys(self):
        """Test GeminiLLM initialization with multiple API keys."""
        keys = ["key1", "key2", "key3"]
        llm = GeminiLLM(api_keys=keys)

        assert llm.api_key is None
        assert llm.key_rotator is not None
        assert isinstance(llm.key_rotator, KeyRotator)

    def test_initialization_custom_parameters(self):
        """Test GeminiLLM initialization with custom parameters."""
        llm = GeminiLLM(
            api_keys="test-key", model="custom-model", timeout=30.0, temperature=0.5, max_retries=5
        )

        assert llm.model == "custom-model"
        assert llm.timeout == 30.0
        assert llm.temperature == 0.5
        assert llm.max_retries == 5

    def test_initialization_no_api_keys(self):
        """Test GeminiLLM initialization without API keys."""
        with pytest.raises(ConfigurationError, match="API keys must be provided"):
            GeminiLLM(api_keys=None)

    def test_initialization_empty_api_keys(self):
        """Test GeminiLLM initialization with empty API keys."""
        with pytest.raises(ConfigurationError, match="API keys must be provided"):
            GeminiLLM(api_keys=[])

    @patch("cogency.llm.gemini.ChatGoogleGenerativeAI")
    def test_init_current_llm_single_key(self, mock_chat_llm):
        """Test LLM instance initialization with single key."""
        mock_instance = Mock()
        mock_chat_llm.return_value = mock_instance

        llm = GeminiLLM(api_keys="test-key")

        mock_chat_llm.assert_called_once_with(
            model="gemini-2.5-flash",
            google_api_key="test-key",
            timeout=15.0,
            temperature=0.7,
            max_retries=3,
        )
        assert llm._current_llm == mock_instance

    @patch("cogency.llm.gemini.ChatGoogleGenerativeAI")
    def test_init_current_llm_key_rotator(self, mock_chat_llm):
        """Test LLM instance initialization with key rotator."""
        mock_instance = Mock()
        mock_chat_llm.return_value = mock_instance

        llm = GeminiLLM(api_keys=["key1", "key2"])  # noqa: F841

        # Should use first key from rotator
        mock_chat_llm.assert_called_once()
        call_args = mock_chat_llm.call_args
        assert call_args[1]["google_api_key"] in ["key1", "key2"]

    def test_init_current_llm_no_key(self):
        """Test LLM instance initialization without valid key."""
        # Mock a scenario where key_rotator returns None
        with patch.object(KeyRotator, "get_key", return_value=None):
            with pytest.raises(ConfigurationError, match="API key must be provided"):
                GeminiLLM(api_keys=["key1", "key2"])

    @patch("cogency.llm.gemini.ChatGoogleGenerativeAI")
    @pytest.mark.asyncio
    async def test_invoke_single_key(self, mock_chat_llm):
        """Test invoke method with single key."""
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = AsyncMock(content="LLM response")
        mock_chat_llm.return_value = mock_instance

        llm = GeminiLLM(api_keys="test-key")

        messages = [{"role": "user", "content": "Hello"}]
        result = await llm.invoke(messages)

        assert result == "LLM response"
        mock_instance.ainvoke.assert_called_once_with(messages)

    @patch("cogency.llm.gemini.ChatGoogleGenerativeAI")
    @pytest.mark.asyncio
    async def test_invoke_with_key_rotation(self, mock_chat_llm):
        """Test invoke method with key rotation."""
        mock_instance1 = AsyncMock()
        mock_instance1.ainvoke.return_value = AsyncMock(content="LLM response")
        mock_instance2 = AsyncMock()
        mock_instance2.ainvoke.return_value = AsyncMock(content="LLM response")

        # Mock different instances for different keys
        mock_chat_llm.side_effect = [mock_instance1, mock_instance2]

        llm = GeminiLLM(api_keys=["key1", "key2"])

        messages = [{"role": "user", "content": "Hello"}]

        # First invoke
        result1 = await llm.invoke(messages)
        assert result1 == "LLM response"

        # Second invoke should potentially use different key
        result2 = await llm.invoke(messages)
        assert result2 == "LLM response"

    @patch("cogency.llm.gemini.ChatGoogleGenerativeAI")
    @pytest.mark.asyncio
    async def test_invoke_no_current_llm(self, mock_chat_llm):
        """Test invoke method when current LLM is None."""
        mock_chat_llm.return_value = None

        llm = GeminiLLM(api_keys="test-key")
        llm._current_llm = None  # Force None state

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RuntimeError, match="LLM instance not initialized"):
            await llm.invoke(messages)

    @patch("cogency.llm.gemini.ChatGoogleGenerativeAI")
    def test_llm_instance_caching(self, mock_chat_llm):
        """Test that LLM instances are cached by key."""
        mock_instance1 = Mock()
        mock_instance2 = Mock()
        mock_chat_llm.side_effect = [mock_instance1, mock_instance2]

        # Create LLM with key rotation
        llm = GeminiLLM(api_keys=["key1", "key2"])

        # Force specific key usage and verify caching
        with patch.object(llm.key_rotator, "get_key", side_effect=["key1", "key1", "key2", "key2"]):
            # First call to key1 - should create instance
            llm._init_current_llm()
            first_instance = llm._current_llm

            # Second call to key1 - should reuse cached instance
            llm._init_current_llm()
            assert llm._current_llm == first_instance

            # First call to key2 - should create new instance
            llm._init_current_llm()
            second_instance = llm._current_llm
            assert second_instance != first_instance

            # Second call to key2 - should reuse cached instance
            llm._init_current_llm()
            assert llm._current_llm == second_instance

        # Should have called ChatGoogleGenerativeAI twice (once per unique key)
        assert mock_chat_llm.call_count == 2

    @patch("cogency.llm.gemini.ChatGoogleGenerativeAI")
    @pytest.mark.asyncio
    async def test_invoke_with_additional_kwargs(self, mock_chat_llm):
        """Test invoke method with additional keyword arguments."""
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = AsyncMock(content="LLM response")
        mock_chat_llm.return_value = mock_instance

        llm = GeminiLLM(api_keys="test-key")

        messages = [{"role": "user", "content": "Hello"}]
        additional_kwargs = {"stream": True, "max_tokens": 100}

        result = await llm.invoke(messages, **additional_kwargs)

        assert result == "LLM response"
        mock_instance.ainvoke.assert_called_once_with(messages, **additional_kwargs)

    def test_kwargs_construction(self):
        """Test that kwargs are properly constructed for ChatGoogleGenerativeAI."""
        with pytest.warns(UserWarning, match="custom_param"):
            llm = GeminiLLM(
                api_keys="test-key",
                timeout=25.0,
                temperature=0.8,
                max_retries=2,
                custom_param="custom_value",
            )

        expected_kwargs = {
            "timeout": 25.0,
            "temperature": 0.8,
            "max_retries": 2,
            "custom_param": "custom_value",
        }

        assert llm.kwargs == expected_kwargs
