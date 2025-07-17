import pytest
from unittest.mock import Mock, AsyncMock, patch
from cogency.llm.grok import GrokLLM
from cogency.utils.errors import ConfigurationError


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing Grok."""
    client = Mock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def mock_grok_response():
    """Mock Grok response for testing."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message.content = "Test response"
    return response


@pytest.fixture
def mock_grok_stream():
    """Mock Grok stream for testing."""
    chunk1 = Mock()
    chunk1.choices = [Mock()]
    chunk1.choices[0].delta.content = "Test "
    
    chunk2 = Mock()
    chunk2.choices = [Mock()]
    chunk2.choices[0].delta.content = "stream"
    
    async def async_iter():
        yield chunk1
        yield chunk2
    
    return async_iter()


@pytest.mark.asyncio
class TestGrokLLM:
    
    def test_init_with_api_key(self):
        with patch('openai.AsyncOpenAI') as mock_openai:
            llm = GrokLLM(api_keys="test-key")
            assert llm.api_key == "test-key"
            assert llm.model == "grok-beta"
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://api.x.ai/v1"
            )
    
    def test_init_with_api_key_list(self):
        with patch('openai.AsyncOpenAI') as mock_openai:
            llm = GrokLLM(api_keys=["key1", "key2"])
            assert llm.key_rotator is not None
            assert llm.api_key is None
    
    def test_init_without_api_key_raises_error(self):
        with pytest.raises(ConfigurationError, match="API keys must be provided"):
            GrokLLM(api_keys=None)
    
    def test_init_with_custom_model(self):
        with patch('openai.AsyncOpenAI'):
            llm = GrokLLM(api_keys="test-key", model="grok-2")
            assert llm.model == "grok-2"
    
    def test_init_with_custom_params(self):
        with patch('openai.AsyncOpenAI'):
            llm = GrokLLM(
                api_keys="test-key",
                temperature=0.5,
                timeout=30.0,
                max_retries=5
            )
            assert llm.temperature == 0.5
            assert llm.timeout == 30.0
            assert llm.max_retries == 5
    
    async def test_invoke(self, mock_openai_client, mock_grok_response):
        mock_openai_client.chat.completions.create.return_value = mock_grok_response
        
        with patch('openai.AsyncOpenAI', return_value=mock_openai_client):
            llm = GrokLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            result = await llm.invoke(messages)
            
            assert result == "Test response"
            mock_openai_client.chat.completions.create.assert_called_once_with(
                model="grok-beta",
                messages=messages,
                timeout=15.0,
                temperature=0.7,
                max_retries=3
            )
    
    async def test_stream(self, mock_openai_client, mock_grok_stream):
        mock_openai_client.chat.completions.create.return_value = mock_grok_stream
        
        with patch('openai.AsyncOpenAI', return_value=mock_openai_client):
            llm = GrokLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            chunks = []
            async for chunk in llm.stream(messages):
                chunks.append(chunk)
            
            assert chunks == ["Test ", "stream"]
            mock_openai_client.chat.completions.create.assert_called_once_with(
                model="grok-beta",
                messages=messages,
                stream=True,
                timeout=15.0,
                temperature=0.7,
                max_retries=3
            )
    
    async def test_stream_with_none_content(self, mock_openai_client):
        chunk_with_none = Mock()
        chunk_with_none.choices = [Mock()]
        chunk_with_none.choices[0].delta.content = None
        
        chunk_with_content = Mock()
        chunk_with_content.choices = [Mock()]
        chunk_with_content.choices[0].delta.content = "content"
        
        async def async_iter():
            yield chunk_with_none
            yield chunk_with_content
        
        mock_openai_client.chat.completions.create.return_value = async_iter()
        
        with patch('openai.AsyncOpenAI', return_value=mock_openai_client):
            llm = GrokLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            chunks = []
            async for chunk in llm.stream(messages):
                chunks.append(chunk)
            
            assert chunks == ["content"]
    
    def test_convert_msgs(self):
        with patch('openai.AsyncOpenAI'):
            llm = GrokLLM(api_keys="test-key")
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
            
            converted = llm._convert_msgs(messages)
            
            assert converted == [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
    
    def test_key_rotation(self):
        with patch('openai.AsyncOpenAI') as mock_openai:
            llm = GrokLLM(api_keys=["key1", "key2"])
            
            # Should rotate and reinitialize client
            llm._rotate_client()
            
            # Should have been called at least twice (init + rotate)
            assert mock_openai.call_count >= 2
    
    def test_base_url_correct(self):
        with patch('openai.AsyncOpenAI') as mock_openai:
            GrokLLM(api_keys="test-key")
            
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://api.x.ai/v1"
            )