from unittest.mock import MagicMock, patch

import pytest

from cogency.tools import Scrape


@pytest.fixture
def mock_trafilatura():
    # Mock trafilatura module in sys.modules
    with patch.dict("sys.modules", {"trafilatura": MagicMock()}) as mock_sys_modules:
        # Get the mocked trafilatura module
        mock_lib = mock_sys_modules["trafilatura"]
        yield mock_lib


@pytest.mark.asyncio
async def test_scrape_success(mock_trafilatura):
    tool = Scrape()
    mock_trafilatura.fetch_url.return_value = "<html><body><p>Test content</p></body></html>"
    mock_trafilatura.extract.return_value = "Test content"

    result = await tool.execute(url="http://example.com")

    assert not result.error
    assert "Scraped example.com" in result.outcome
    assert "Test content" in result.content
    mock_trafilatura.fetch_url.assert_called_once_with("http://example.com")
    mock_trafilatura.extract.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_empty_url():
    tool = Scrape()
    result = await tool.execute(url="")

    assert result.error
    assert "URL cannot be empty" in result.outcome


@pytest.mark.asyncio
async def test_scrape_fetch_failure(mock_trafilatura):
    tool = Scrape()
    mock_trafilatura.fetch_url.return_value = None

    result = await tool.execute(url="http://example.com")

    assert result.error
    assert "Failed to fetch content from: http://example.com" in result.outcome


@pytest.mark.asyncio
async def test_scrape_no_readable_content(mock_trafilatura):
    tool = Scrape()
    mock_trafilatura.fetch_url.return_value = "<html><body></body></html>"
    mock_trafilatura.extract.return_value = None

    result = await tool.execute(url="http://example.com")

    assert not result.error
    assert "Scraped example.com" in result.outcome
    assert "No readable content found" in result.content


@pytest.mark.asyncio
async def test_scrape_truncation(mock_trafilatura):
    tool = Scrape()
    long_content = "a" * 5000  # Exceeds SCRAPE_LIMIT (3000)
    mock_trafilatura.fetch_url.return_value = "<html><body>" + long_content + "</body></html>"
    mock_trafilatura.extract.return_value = long_content

    result = await tool.execute(url="http://example.com")

    assert not result.error
    assert "Scraped example.com" in result.outcome
    assert len(result.content) < len(long_content)
    assert "[Content continues...]" in result.content
