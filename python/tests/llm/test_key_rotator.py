"""Tests for KeyRotator implementation."""

import pytest

from cogency.llm.key_rotator import KeyRotator


class TestKeyRotator:
    """Test suite for KeyRotator."""

    def test_initialization(self):
        """Test KeyRotator initialization."""
        keys = ["key1", "key2", "key3"]
        rotator = KeyRotator(keys)

        assert rotator.keys == keys

    def test_single_key_rotation(self):
        """Test rotation with single key."""
        rotator = KeyRotator(["single-key"])

        # Should always return the same key
        assert rotator.get_key() == "single-key"
        assert rotator.get_key() == "single-key"
        assert rotator.get_key() == "single-key"

    def test_multiple_key_rotation(self):
        """Test rotation with multiple keys."""
        keys = ["key1", "key2", "key3"]
        rotator = KeyRotator(keys)

        # Should cycle through keys in order
        assert rotator.get_key() == "key1"
        assert rotator.get_key() == "key2"
        assert rotator.get_key() == "key3"

        # Should cycle back to beginning
        assert rotator.get_key() == "key1"
        assert rotator.get_key() == "key2"

    def test_two_key_rotation(self):
        """Test rotation with two keys."""
        rotator = KeyRotator(["key1", "key2"])

        # Should alternate between keys
        assert rotator.get_key() == "key1"
        assert rotator.get_key() == "key2"
        assert rotator.get_key() == "key1"
        assert rotator.get_key() == "key2"

    def test_empty_keys_list(self):
        """Test KeyRotator with empty keys list."""
        rotator = KeyRotator([])

        # Should raise StopIteration when cycling empty list
        with pytest.raises(StopIteration):
            rotator.get_key()

    def test_rotation_order_consistency(self):
        """Test that rotation order is consistent across multiple instances."""
        keys = ["a", "b", "c", "d"]

        rotator1 = KeyRotator(keys)
        rotator2 = KeyRotator(keys)

        # Both rotators should return keys in same order
        for _ in range(10):
            assert rotator1.get_key() == rotator2.get_key()

    def test_rotation_independence(self):
        """Test that different rotator instances are independent."""
        keys = ["key1", "key2", "key3"]

        rotator1 = KeyRotator(keys)
        rotator2 = KeyRotator(keys)

        # Advance first rotator
        rotator1.get_key()  # key1
        rotator1.get_key()  # key2

        # Second rotator should still start from beginning
        assert rotator2.get_key() == "key1"
        assert rotator1.get_key() == "key3"  # First continues from where it left off

    def test_keys_immutability(self):
        """Test that modifying original keys list doesn't affect rotator."""
        keys = ["key1", "key2"]
        rotator = KeyRotator(keys)

        # Modify original list
        keys.append("key3")
        keys[0] = "modified-key1"

        # Rotator should still use original keys
        assert rotator.get_key() == "key1"  # Not "modified-key1"
        assert rotator.get_key() == "key2"
        assert rotator.get_key() == "key1"  # Not "key3"

    def test_large_number_of_keys(self):
        """Test rotation with large number of keys."""
        keys = [f"key{i}" for i in range(100)]
        rotator = KeyRotator(keys)

        # Test that all keys are returned in order
        for i in range(100):
            assert rotator.get_key() == f"key{i}"

        # Test that it cycles back
        assert rotator.get_key() == "key0"

    def test_rotation_state_persistence(self):
        """Test that rotation state persists between calls."""
        rotator = KeyRotator(["a", "b", "c"])

        # Get some keys
        first = rotator.get_key()  # a
        second = rotator.get_key()  # b

        # Pause, then continue
        third = rotator.get_key()  # c
        fourth = rotator.get_key()  # a (back to start)

        assert [first, second, third, fourth] == ["a", "b", "c", "a"]

    def test_string_keys(self):
        """Test rotation with string keys."""
        rotator = KeyRotator(["alpha", "beta", "gamma"])

        assert rotator.get_key() == "alpha"
        assert rotator.get_key() == "beta"
        assert rotator.get_key() == "gamma"
        assert rotator.get_key() == "alpha"

    def test_duplicate_keys(self):
        """Test rotation with duplicate keys."""
        rotator = KeyRotator(["key1", "key2", "key1", "key3"])

        # Should include duplicates in rotation
        assert rotator.get_key() == "key1"
        assert rotator.get_key() == "key2"
        assert rotator.get_key() == "key1"  # Duplicate
        assert rotator.get_key() == "key3"
        assert rotator.get_key() == "key1"  # Back to start
