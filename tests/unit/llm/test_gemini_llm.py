import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from cogency.llm.gemini import GeminiLLM
from cogency.utils.errors import ConfigurationError
from cogency.resilience import RateLimitedError


@pytest.fixture
def mock_gemini_model():
    """Mock Gemini model for testing."""
    model = Mock()
    model.generate_content_async = AsyncMock()
    return model


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini response for testing."""
    response = Mock()
    response.text = "Test response"
    return response


@pytest.fixture
def mock_gemini_stream():
    """Mock Gemini stream for testing."""
    chunk1 = Mock()
    chunk1.text = "Test "
    
    chunk2 = Mock()
    chunk2.text = "stream"
    
    async def async_iter():
        yield chunk1
        yield chunk2
    
    return async_iter()


@pytest.mark.asyncio
class TestGeminiLLM:
    
    def test_init_with_api_key(self):
        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('google.generativeai.configure') as mock_config:
            llm = GeminiLLM(api_keys="test-key")
            assert llm.api_key == "test-key"
            assert llm.model == "gemini-2.5-flash"
            mock_config.assert_called_once_with(api_key="test-key")
            mock_model.assert_called_once()
    
    def test_init_with_api_key_list(self):
        with patch('google.generativeai.GenerativeModel'), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys=["key1", "key2"])
            assert llm.key_rotator is not None
            assert llm.api_key is None
    
    def test_init_with_env_vars(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY_1': 'env-key-1', 'GEMINI_API_KEY_2': 'env-key-2'}), \
             patch('google.generativeai.GenerativeModel'), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM()
            assert llm.key_rotator is not None
    
    def test_init_with_fallback_env_var(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'fallback-key'}, clear=True), \
             patch('google.generativeai.GenerativeModel'), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM()
            assert llm.api_key == "fallback-key"
    
    def test_init_without_api_key_raises_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError, match="API keys must be provided"):
                GeminiLLM()
    
    def test_init_with_custom_model(self):
        with patch('google.generativeai.GenerativeModel'), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys="test-key", model="gemini-pro")
            assert llm.model == "gemini-pro"
    
    def test_init_with_custom_params(self):
        with patch('google.generativeai.GenerativeModel'), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(
                api_keys="test-key",
                temperature=0.5,
                timeout=30.0,
                max_retries=5
            )
            assert llm.temperature == 0.5
            assert llm.timeout == 30.0
            assert llm.max_retries == 5
    
    async def test_invoke(self, mock_gemini_model, mock_gemini_response):
        mock_gemini_model.generate_content_async.return_value = mock_gemini_response
        
        with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            result = await llm.invoke(messages)
            
            assert result == "Test response"
            mock_gemini_model.generate_content_async.assert_called_once_with("user: Hello")
    
    async def test_stream(self, mock_gemini_model, mock_gemini_stream):
        mock_gemini_model.generate_content_async.return_value = mock_gemini_stream
        
        with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            chunks = []
            async for chunk in llm.stream(messages):
                chunks.append(chunk)
            
            assert chunks == ["Test ", "stream"]
            mock_gemini_model.generate_content_async.assert_called_once_with(
                "user: Hello", 
                stream=True
            )
    
    async def test_stream_with_none_text(self, mock_gemini_model):
        chunk_with_none = Mock()
        chunk_with_none.text = None
        
        chunk_with_content = Mock()
        chunk_with_content.text = "content"
        
        async def async_iter():
            yield chunk_with_none
            yield chunk_with_content
        
        mock_gemini_model.generate_content_async.return_value = async_iter()
        
        with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            chunks = []
            async for chunk in llm.stream(messages):
                chunks.append(chunk)
            
            assert chunks == ["content"]
    
    async def test_invoke_rate_limit_error(self, mock_gemini_model):
        mock_gemini_model.generate_content_async.side_effect = Exception("429 quota exceeded")
        
        with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(RateLimitedError):
                await llm.invoke(messages)
    
    async def test_stream_rate_limit_error(self, mock_gemini_model):
        async def failing_iter():
            raise Exception("quota exceeded")
        
        mock_gemini_model.generate_content_async.return_value = failing_iter()
        
        with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(RateLimitedError):
                async for chunk in llm.stream(messages):
                    pass
    
    def test_key_rotation(self):
        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('google.generativeai.configure') as mock_config:
            llm = GeminiLLM(api_keys=["key1", "key2"])
            
            # Should rotate and reinitialize client
            llm._rotate_client()
            
            # Should have been called at least twice (init + rotate)
            assert mock_config.call_count >= 2
    
    def test_generation_config_params(self):
        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('google.generativeai.configure'), \
             patch('google.generativeai.types.GenerationConfig') as mock_config:
            
            GeminiLLM(
                api_keys="test-key",
                temperature=0.5,
                timeout=30.0,  # Should be filtered out
                max_retries=5   # Should be filtered out
            )
            
            # Only GenerationConfig-compatible params should be passed
            mock_config.assert_called_once_with(temperature=0.5)
    
    def test_message_formatting(self):
        with patch('google.generativeai.GenerativeModel'), \
             patch('google.generativeai.configure'):
            llm = GeminiLLM(api_keys="test-key")
            
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
            
            # Test that messages are formatted correctly
            formatted = "".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            assert formatted == "user: Helloassistant: Hi there"