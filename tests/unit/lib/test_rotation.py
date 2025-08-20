"""Minimal rotation tests - essential coverage only."""

import os
import pytest
from unittest.mock import patch
from cogency.lib.rotation import Rotator, with_rotation, _rotators


def setup_function():
    """Clear global state."""
    _rotators.clear()


def test_rotation_basics():
    """Test core rotation functionality."""
    with patch.dict(os.environ, {
        "TEST_API_KEY_1": "key1",
        "TEST_API_KEY_2": "key2"
    }, clear=True):
        rotator = Rotator("test")
        
        # Keys loaded correctly
        assert rotator.keys == ["key1", "key2"]
        assert rotator.current_key() == "key1"
        
        # Rotation works on rate limits
        with patch('cogency.lib.rotation.time.time', side_effect=[2, 4]):
            assert rotator.rotate("Rate limit exceeded") is True
            assert rotator.current_key() == "key2"


def test_rate_limit_detection():
    """Test rate limit signal detection.""" 
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        rotator = Rotator("test")
        
        # Rate limit signals trigger rotation (with time progression)
        with patch('cogency.lib.rotation.time.time', side_effect=[2, 4, 6]):
            assert rotator.rotate("quota exceeded") is True
            assert rotator.rotate("429 error") is True  
            assert rotator.rotate("throttle limit") is True
            
        # Non-rate-limit errors don't trigger rotation
        assert rotator.rotate("invalid key") is False
        assert rotator.rotate("connection error") is False


@pytest.mark.asyncio
async def test_wrapper_function():
    """Test with_rotation wrapper."""
    with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}, clear=True):
        
        async def mock_api(api_key):
            assert api_key == "test_key"
            return "success"
        
        result = await with_rotation("TEST", mock_api)
        assert result == "success"


@pytest.mark.asyncio  
async def test_provider_integration():
    """Test real provider pattern."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "real_key"}, clear=True):
        
        async def _generate(api_key):
            assert api_key == "real_key"
            return "Generated text"
        
        result = await with_rotation("GEMINI", _generate)
        assert result == "Generated text"