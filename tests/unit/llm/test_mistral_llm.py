import pytest
from unittest.mock import Mock, AsyncMock, patch
from cogency.llm.mistral import MistralLLM
from cogency.utils.errors import ConfigurationError


@pytest.fixture
def mock_mistral_client():
    """Mock Mistral client for testing."""
    client = Mock()
    client.chat.complete_async = AsyncMock()
    client.chat.stream_async = AsyncMock()
    return client


@pytest.fixture
def mock_mistral_response():
    """Mock Mistral response for testing."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message.content = "Test response"
    return response


@pytest.fixture
def mock_mistral_stream():
    """Mock Mistral stream for testing."""
    chunk1 = Mock()
    chunk1.data.choices = [Mock()]
    chunk1.data.choices[0].delta.content = "Test "
    
    chunk2 = Mock()
    chunk2.data.choices = [Mock()]
    chunk2.data.choices[0].delta.content = "stream"
    
    async def async_iter():
        yield chunk1
        yield chunk2
    
    return async_iter()


@pytest.mark.asyncio
class TestMistralLLM:
    
    def test_init_with_api_key(self):
        with patch('cogency.llm.mistral.Mistral') as mock_mistral:
            llm = MistralLLM(api_keys="test-key")
            assert llm.api_key == "test-key"
            assert llm.model == "mistral-large-latest"
            mock_mistral.assert_called_once_with(api_key="test-key")
    
    def test_init_with_api_key_list(self):
        with patch('cogency.llm.mistral.Mistral') as mock_mistral:
            llm = MistralLLM(api_keys=["key1", "key2"])
            assert llm.key_rotator is not None
            assert llm.api_key is None
    
    def test_init_without_api_key_raises_error(self):
        with pytest.raises(ConfigurationError, match="API keys must be provided"):
            MistralLLM(api_keys=None)
    
    def test_init_with_custom_model(self):
        with patch('cogency.llm.mistral.Mistral'):
            llm = MistralLLM(api_keys="test-key", model="mistral-small")
            assert llm.model == "mistral-small"
    
    def test_init_with_custom_params(self):
        with patch('cogency.llm.mistral.Mistral'):
            llm = MistralLLM(
                api_keys="test-key",
                temperature=0.5,
                max_tokens=2048,
                timeout=30.0
            )
            assert llm.temperature == 0.5
            assert llm.max_tokens == 2048
            assert llm.timeout == 30.0
    
    async def test_invoke(self, mock_mistral_client, mock_mistral_response):
        mock_mistral_client.chat.complete_async.return_value = mock_mistral_response
        
        with patch('cogency.llm.mistral.Mistral', return_value=mock_mistral_client):
            llm = MistralLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            result = await llm.invoke(messages)
            
            assert result == "Test response"
            mock_mistral_client.chat.complete_async.assert_called_once_with(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.7,
                max_tokens=4096
            )
    
    async def test_stream(self, mock_mistral_client, mock_mistral_stream):
        mock_mistral_client.chat.stream_async.return_value = mock_mistral_stream
        
        with patch('cogency.llm.mistral.Mistral', return_value=mock_mistral_client):
            llm = MistralLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            chunks = []
            async for chunk in llm.stream(messages):
                chunks.append(chunk)
            
            assert chunks == ["Test ", "stream"]
            mock_mistral_client.chat.stream_async.assert_called_once_with(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.7,
                max_tokens=4096
            )
    
    async def test_stream_with_none_content(self, mock_mistral_client):
        chunk_with_none = Mock()
        chunk_with_none.data.choices = [Mock()]
        chunk_with_none.data.choices[0].delta.content = None
        
        chunk_with_content = Mock()
        chunk_with_content.data.choices = [Mock()]
        chunk_with_content.data.choices[0].delta.content = "content"
        
        async def async_iter():
            yield chunk_with_none
            yield chunk_with_content
        
        mock_mistral_client.chat.stream_async.return_value = async_iter()
        
        with patch('cogency.llm.mistral.Mistral', return_value=mock_mistral_client):
            llm = MistralLLM(api_keys="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            chunks = []
            async for chunk in llm.stream(messages):
                chunks.append(chunk)
            
            assert chunks == ["content"]
    
    def test_convert_msgs(self):
        with patch('cogency.llm.mistral.Mistral'):
            llm = MistralLLM(api_keys="test-key")
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
        with patch('cogency.llm.mistral.Mistral') as mock_mistral:
            llm = MistralLLM(api_keys=["key1", "key2"])
            
            # Should rotate and reinitialize client
            llm._rotate_client()
            
            # Should have been called at least twice (init + rotate)
            assert mock_mistral.call_count >= 2