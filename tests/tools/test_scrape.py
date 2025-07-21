"""Test Scrape tool business logic."""

from unittest.mock import MagicMock, patch

import pytest

from cogency.tools.scrape import Scrape


class TestScrape:
    """Test Scrape tool business logic."""

    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Scrape tool implements required interface."""
        scrape = Scrape()

        # Required attributes
        assert scrape.name == "scrape"
        assert scrape.description
        assert hasattr(scrape, "run")

        # Schema and examples
        schema = scrape.schema()
        examples = scrape.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0

    @pytest.mark.asyncio
    async def test_invalid_url(self):
        """Scrape tool handles invalid URLs."""
        scrape = Scrape()

        # Test None URL
        result = await scrape.run(url=None)
        assert result["success"] is False
        assert "required" in result["error"].lower()

        # Test empty URL
        result = await scrape.run(url="")
        assert result["success"] is False
        assert "required" in result["error"].lower()

        # Test non-string URL
        result = await scrape.run(url=123)
        assert result["success"] is False
        assert "string" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("trafilatura.fetch_url")
    @patch("trafilatura.extract")
    @patch("trafilatura.extract_metadata")
    async def test_successful_extraction(self, mock_metadata, mock_extract, mock_fetch):
        """Scrape tool successfully extracts content."""
        scrape = Scrape()

        # Mock successful fetch
        mock_html = "<html><body>Test content</body></html>"
        mock_fetch.return_value = mock_html

        # Mock successful extraction
        mock_content = "This is the main article content."
        mock_extract.return_value = mock_content

        # Mock metadata
        mock_meta = MagicMock()
        mock_meta.title = "Test Article"
        mock_meta.author = "Test Author"
        mock_meta.date = "2024-01-01"
        mock_meta.url = "https://example.com"
        mock_metadata.return_value = mock_meta

        result = await scrape.run(url="https://example.com")

        assert result["success"] is True
        assert result["content"] == mock_content
        assert result["url"] == "https://example.com"
        assert result["metadata"]["title"] == "Test Article"
        assert result["metadata"]["author"] == "Test Author"
        assert result["metadata"]["date"] == "2024-01-01"

        # Verify trafilatura was called correctly
        mock_fetch.assert_called_once_with("https://example.com")
        mock_extract.assert_called_once_with(
            mock_html,
            favor_precision=True,
            include_comments=False,
            include_tables=False,
            no_fallback=True,
        )

    @pytest.mark.asyncio
    @patch("trafilatura.fetch_url")
    async def test_fetch_failure(self, mock_fetch):
        """Scrape tool handles fetch failure."""
        scrape = Scrape()

        # Mock failed fetch (returns None)
        mock_fetch.return_value = None

        result = await scrape.run(url="https://example.com")

        assert result["success"] is False
        assert "Could not fetch content" in result["error"]
        assert result["content"] is None
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    @patch("trafilatura.fetch_url")
    @patch("trafilatura.extract")
    async def test_extraction_failure(self, mock_extract, mock_fetch):
        """Scrape tool handles extraction failure."""
        scrape = Scrape()

        # Mock successful fetch but failed extraction
        mock_fetch.return_value = "<html><body>content</body></html>"
        mock_extract.return_value = None

        result = await scrape.run(url="https://example.com")

        assert result["success"] is False
        assert "Could not extract content" in result["error"]
        assert result["content"] is None
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    @patch("trafilatura.fetch_url")
    async def test_extraction_exception(self, mock_fetch):
        """Scrape tool handles exceptions during extraction."""
        scrape = Scrape()

        # Mock exception during fetch
        mock_fetch.side_effect = Exception("Network error")

        result = await scrape.run(url="https://example.com")

        assert result["success"] is False
        assert "Scraping failed" in result["error"]
        assert "Network error" in result["error"]
        assert result["content"] is None
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    @patch("trafilatura.fetch_url")
    @patch("trafilatura.extract")
    async def test_favor_precision_parameter(self, mock_extract, mock_fetch):
        """Scrape tool correctly passes favor_precision parameter."""
        scrape = Scrape()

        mock_fetch.return_value = "<html><body>content</body></html>"
        mock_extract.return_value = "content"

        # Test with favor_precision=False
        await scrape.run(url="https://example.com", favor_precision=False)

        mock_extract.assert_called_with(
            "<html><body>content</body></html>",
            favor_precision=False,
            include_comments=False,
            include_tables=False,
            no_fallback=True,
        )

    @pytest.mark.asyncio
    @patch("trafilatura.fetch_url")
    @patch("trafilatura.extract")
    @patch("trafilatura.extract_metadata")
    async def test_metadata_handling(self, mock_metadata, mock_extract, mock_fetch):
        """Scrape tool handles missing metadata gracefully."""
        scrape = Scrape()

        mock_fetch.return_value = "<html><body>content</body></html>"
        mock_extract.return_value = "content"

        # Test with None metadata
        mock_metadata.return_value = None

        result = await scrape.run(url="https://example.com")

        assert result["success"] is True
        assert result["metadata"]["title"] is None
        assert result["metadata"]["author"] is None
        assert result["metadata"]["date"] is None
        assert result["metadata"]["url"] == "https://example.com"

        # Test with partial metadata
        mock_meta = MagicMock()
        mock_meta.title = "Title Only"
        mock_meta.author = None
        mock_meta.date = None
        mock_meta.url = None
        mock_metadata.return_value = mock_meta

        result = await scrape.run(url="https://example.com")

        assert result["metadata"]["title"] == "Title Only"
        assert result["metadata"]["author"] is None
        assert result["metadata"]["date"] is None
        assert result["metadata"]["url"] == "https://example.com"
