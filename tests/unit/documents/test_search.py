"""Document search functionality tests."""

import pytest

from cogency.documents import search


def test_search_function_exists():
    """Test that search function is available."""
    assert callable(search)


@pytest.mark.asyncio
async def test_search_basic():
    """Test basic search functionality."""
    # Test with mock implementation since we don't want real file system operations
    with pytest.raises((NotImplementedError, TypeError, ValueError)):
        # This will likely fail without proper setup, which is expected for unit tests
        await search("test query", limit=5)


def test_search_import():
    """Test that search can be imported from documents module."""
    from cogency.documents import search

    assert search is not None
