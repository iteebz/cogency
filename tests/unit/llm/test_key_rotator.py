
import pytest
from cogency.llm.key_rotator import KeyRotator

def test_key_rotator_get_key():
    """Test that get_key cycles through keys correctly."""
    rotator = KeyRotator(["key1", "key2", "key3"])
    assert rotator.get_key() == "key1"
    assert rotator.get_key() == "key2"
    assert rotator.get_key() == "key3"
    assert rotator.get_key() == "key1"

def test_key_rotator_rotate_key():
    """Test that rotate_key advances to the next key and returns feedback."""
    rotator = KeyRotator(["key1", "key2"])
    assert rotator.get_key() == "key1"
    assert rotator.rotate_key() == "Rate limited, rotating to next key"
    assert rotator.current_key == "key2"
    assert rotator.rotate_key() == "Rate limited, rotating to next key"
    assert rotator.current_key == "key1"

def test_key_rotator_single_key():
    """Test KeyRotator with a single key."""
    rotator = KeyRotator(["single_key"])
    assert rotator.get_key() == "single_key"
    assert rotator.get_key() == "single_key"
    assert rotator.rotate_key() == "Rate limited, rotating to next key"
    assert rotator.current_key == "single_key"
