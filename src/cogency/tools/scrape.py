"""Scrape tool - web content extraction."""

from ..core.protocols import Tool
from ..lib.result import Err, Ok, Result
from .security import validate_input


class Scrape(Tool):
    """Extract content from web pages."""

    @property
    def name(self) -> str:
        return "scrape"

    @property
    def description(self) -> str:
        return "Extract text content from a web page. Args: url (str)"

    async def execute(self, url: str) -> Result[str, str]:
        """Execute web scraping."""
        try:
            # Import here to handle optional dependency gracefully
            import trafilatura
        except ImportError:
            return Err("Web scraping not available - install trafilatura")

        if not url:
            return Err("URL cannot be empty")

        if not validate_input(url):
            return Err("Invalid URL provided")

        try:
            # Fetch and extract content
            content = trafilatura.fetch_url(url)
            if not content:
                return Err(f"Failed to fetch content from: {url}")

            extracted = trafilatura.extract(content)
            if not extracted:
                return Err(f"Failed to extract text from: {url}")

            return Ok(extracted)

        except Exception as e:
            return Err(f"Scraping failed: {str(e)}")
