"""Scrape tool tests."""

from unittest.mock import patch

import pytest

from cogency.tools.scrape import Scrape


def test_init():
    """Scrape initialization."""
    scrape = Scrape()
    assert scrape.name == "scrape"
    assert "extract text content" in scrape.description.lower()
    assert "url" in scrape.description


@pytest.mark.asyncio
async def test_execute_success():
    """Scrape extracts content from URL."""
    scrape = Scrape()

    with patch("trafilatura.fetch_url") as mock_fetch, patch("trafilatura.extract") as mock_extract:
        mock_fetch.return_value = "<html>content</html>"
        mock_extract.return_value = "Clean text content"

        result = await scrape.execute("https://example.com")

        assert result.success
        assert "Clean text content" in result.unwrap()
        mock_fetch.assert_called_once_with("https://example.com")
        mock_extract.assert_called_once()


@pytest.mark.asyncio
async def test_execute_empty_url():
    """Scrape rejects empty URL."""
    scrape = Scrape()
    result = await scrape.execute("")

    assert result.failure
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_invalid_url():
    """Scrape validates URL input."""
    scrape = Scrape()
    result = await scrape.execute("rm -rf /")

    assert result.failure
    assert "invalid" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_fetch_failed():
    """Scrape handles fetch failure."""
    scrape = Scrape()

    with patch("trafilatura.fetch_url") as mock_fetch, patch("trafilatura.extract") as mock_extract:
        mock_fetch.return_value = None
        mock_extract.return_value = "content"

        result = await scrape.execute("https://example.com")

        assert result.failure
        assert "failed to fetch" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_extract_failed():
    """Scrape handles extraction failure."""
    scrape = Scrape()

    with patch("trafilatura.fetch_url") as mock_fetch, patch("trafilatura.extract") as mock_extract:
        mock_fetch.return_value = "<html>content</html>"
        mock_extract.return_value = None

        result = await scrape.execute("https://example.com")

        assert result.failure
        assert "extract" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_import_error():
    """Scrape handles missing trafilatura."""
    scrape = Scrape()

    with patch("builtins.__import__", side_effect=ImportError("No module")):
        result = await scrape.execute("https://example.com")

        assert result.failure
        assert "not available" in result.error.lower()
        assert "trafilatura" in result.error.lower()
