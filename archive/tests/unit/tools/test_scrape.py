"""Scrape tool tests."""

from unittest.mock import MagicMock, patch

import pytest

from cogency.tools.scrape import Scrape


@pytest.mark.asyncio
@patch("trafilatura.fetch_url")
@patch("trafilatura.extract")
@patch("trafilatura.extract_metadata")
async def test_success(mock_metadata, mock_extract, mock_fetch):
    tool = Scrape()

    mock_fetch.return_value = "<html><body>Content</body></html>"
    mock_extract.return_value = "Clean content"

    mock_meta = MagicMock()
    mock_meta.title = "Test Title"
    mock_metadata.return_value = mock_meta

    result = await tool.run(url="https://example.com")
    assert result.success
    assert result.data["content"] == "Clean content"
    assert result.data["title"] == "Test Title"
    assert result.data["url"] == "https://example.com"


@pytest.mark.asyncio
@patch("trafilatura.fetch_url")
@patch("trafilatura.extract")
@patch("trafilatura.extract_metadata")
async def test_no_title(mock_metadata, mock_extract, mock_fetch):
    tool = Scrape()

    mock_fetch.return_value = "<html><body>Content</body></html>"
    mock_extract.return_value = "Clean content"
    mock_metadata.return_value = None

    result = await tool.run(url="https://example.com")
    assert result.success
    assert result.data["title"] == "Untitled"


@pytest.mark.asyncio
@patch("trafilatura.fetch_url")
async def test_fetch_failure(mock_fetch):
    tool = Scrape()
    mock_fetch.return_value = None

    result = await tool.run(url="https://example.com")
    assert not result.success
    assert "Could not fetch content" in result.error


@pytest.mark.asyncio
@patch("trafilatura.fetch_url")
@patch("trafilatura.extract")
async def test_extract_failure(mock_extract, mock_fetch):
    tool = Scrape()

    mock_fetch.return_value = "<html><body>Content</body></html>"
    mock_extract.return_value = None

    result = await tool.run(url="https://example.com")
    assert not result.success
    assert "Could not extract content" in result.error


@pytest.mark.asyncio
@patch("trafilatura.fetch_url")
async def test_exception(mock_fetch):
    tool = Scrape()
    mock_fetch.side_effect = Exception("Network error")

    result = await tool.run(url="https://example.com")
    assert not result.success
    assert "Scraping failed" in result.error
