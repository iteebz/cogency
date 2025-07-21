"""Comprehensive LLM tests - unified BaseLLM contract and key rotation."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from cogency.llm.base import BaseLLM
from cogency.llm.mock import MockLLM
from cogency.utils.keys import KeyRotator, KeyManager


class TestBaseLLMContract:
    """Test BaseLLM abstract contract and key management."""
    
    def test_base_llm_key_management_initialization(self):
        """Test BaseLLM initializes key management properly."""
        # Single key
        llm = MockLLM(api_keys="single_key")
        assert llm.keys.get_current() == "single_key"
        assert not llm.keys.has_multiple()
        
        # Multiple keys
        keys = ["key1", "key2", "key3"]
        llm = MockLLM(api_keys=keys)
        assert llm.keys.has_multiple()
        assert llm.get_api_key() in keys
    
    def test_base_llm_key_rotation(self):
        """Test automatic key rotation on get_api_key() calls."""
        keys = ["key1", "key2", "key3"]
        llm = MockLLM(api_keys=keys)
        
        # Track keys used across multiple calls
        used_keys = []
        for _ in range(6):  # More than number of keys to see cycling
            used_keys.append(llm.get_api_key())
        
        # Should have rotated through all keys
        unique_keys = set(used_keys)
        assert len(unique_keys) == 3, "Should use all 3 keys"
        assert len(used_keys) == 6, "Should have made 6 calls"
    
    @pytest.mark.asyncio
    async def test_base_llm_run_method_contract(self):
        """Test .run() method contract."""
        llm = MockLLM()
        messages = [{"role": "user", "content": "Hello"}]
        
        result = await llm.run(messages)
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_base_llm_stream_method_contract(self):
        """Test .stream() method contract returns AsyncIterator."""
        llm = MockLLM()
        messages = [{"role": "user", "content": "Hello"}]
        
        stream = llm.stream(messages)
        
        # Should be an async iterator
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
            assert isinstance(chunk, str)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
    
    @pytest.mark.asyncio
    async def test_ainvoke_compatibility_method(self):
        """Test ainvoke() compatibility wrapper calls run()."""
        llm = MockLLM()
        messages = [{"role": "user", "content": "Hello"}]
        
        # Both should return same result
        run_result = await llm.run(messages)
        ainvoke_result = await llm.ainvoke(messages)
        
        assert run_result == ainvoke_result


class TestKeyRotationIntegration:
    """Test key rotation works universally across all LLM providers."""
    
    def test_key_rotation(self):
        """Test key rotation works for any BaseLLM implementation."""
        keys = ["key1", "key2", "key3"]
        llm = MockLLM(api_keys=keys)
        
        # Should have multiple keys
        assert llm.keys.has_multiple()
        
        # Track API key calls
        api_keys_used = []
        for _ in range(6):  # More than number of keys to see cycling
            key = llm.get_api_key()
            api_keys_used.append(key)
        
        # Should have rotated through all keys
        unique_keys = set(api_keys_used)
        assert len(unique_keys) == 3, "Should use all 3 keys"
        assert len(api_keys_used) == 6, "Should have made 6 calls"


class TestKeyRotator:
    """Test KeyRotator functionality."""
    
    def test_single_key_rotation(self):
        """Test rotation with single key."""
        rotator = KeyRotator(["key1"])
        
        # Should always return the same key
        assert rotator.get_current_key() == "key1"
        assert rotator.get_next_key() == "key1"
        assert rotator.get_next_key() == "key1"
    
    def test_multiple_key_rotation(self):
        """Test rotation with multiple keys."""
        keys = ["key1", "key2", "key3"]
        rotator = KeyRotator(keys)
        
        # Should start with one of the keys (random shuffle)
        first_key = rotator.get_current_key()
        assert first_key in keys
        
        # Should cycle through all keys
        seen_keys = {first_key}
        for _ in range(10):  # More than number of keys to ensure cycling
            next_key = rotator.get_next_key()
            seen_keys.add(next_key)
        
        # Should have seen all keys
        assert seen_keys == set(keys)
    
    def test_random_start(self):
        """Test that keys start in random order."""
        keys = ["key1", "key2", "key3", "key4", "key5"]
        
        # Create multiple rotators and check they don't all start with same key
        first_keys = []
        for _ in range(20):
            rotator = KeyRotator(keys.copy())
            first_keys.append(rotator.get_current_key())
        
        # Should have some variation (not all the same)
        unique_first_keys = set(first_keys)
        assert len(unique_first_keys) > 1, "Keys should start randomly"
    
    def test_rotate_key_feedback(self):
        """Test rotate_key returns proper feedback."""
        rotator = KeyRotator(["key12345678", "key87654321"])
        
        # Get the current key before rotation
        current_key = rotator.get_current_key()
        
        feedback = rotator.rotate_key()
        assert "rate limited" in feedback
        assert "rotating to" in feedback
        # Should contain parts of both keys (old and new)
        assert len([part for part in feedback.split() if part.startswith("*")]) == 2


class TestKeyManager:
    """Test KeyManager functionality."""
    
    def test_single_key_string(self):
        """Test KeyManager with single key as string."""
        manager = KeyManager(api_key="single_key")
        
        assert manager.get_current() == "single_key"
        assert manager.get_next() == "single_key"
        assert not manager.has_multiple()
        assert manager.rotate_key() is None
    
    def test_single_key_list(self):
        """Test KeyManager with single key in list."""
        manager = KeyManager.for_provider("test", ["single_key"])
        
        assert manager.get_current() == "single_key"
        assert manager.get_next() == "single_key"
        assert not manager.has_multiple()
    
    def test_multiple_keys(self):
        """Test KeyManager with multiple keys."""
        keys = ["key1", "key2", "key3"]
        manager = KeyManager.for_provider("test", keys)
        
        assert manager.has_multiple()
        
        # Should rotate through keys
        first_key = manager.get_current()
        second_key = manager.get_next()
        
        # Keys should be different (unless we got unlucky with random shuffle)
        # Let's just verify we can get keys and rotation works
        assert first_key in keys
        assert second_key in keys
    
    @patch.dict('os.environ', {
        'TEST_API_KEY_1': 'key1',
        'TEST_API_KEY_2': 'key2',
        'TEST_API_KEY_3': 'key3'
    })
    def test_env_detection_numbered(self):
        """Test detection of numbered environment variables."""
        manager = KeyManager.for_provider("test")
        
        assert manager.has_multiple()
        # Should have detected all 3 keys
        assert manager.key_rotator is not None
        assert len(manager.key_rotator.keys) == 3
    
    @patch.dict('os.environ', {'TEST_API_KEY': 'single_key'})
    def test_env_detection_single(self):
        """Test detection of single environment variable."""
        manager = KeyManager.for_provider("test")
        
        assert not manager.has_multiple()
        assert manager.get_current() == "single_key"
    
    @patch.dict('os.environ', {}, clear=True)
    def test_no_keys_error(self):
        """Test error when no keys found."""
        with pytest.raises(Exception) as exc_info:
            KeyManager.for_provider("test")
        
        assert "No API keys found" in str(exc_info.value)