"""Scrape: Clean web content extraction with intelligent formatting."""

import re
from urllib.parse import urlparse

from ..core.protocols import Tool
from ..lib.result import Err, Ok, Result
from .security import validate_input


class Scrape(Tool):
    """Extract and format web content with clean output."""

    @property
    def name(self) -> str:
        return "scrape"

    @property
    def description(self) -> str:
        return "Extract clean text content from web pages. Args: url (str)"

    @property
    def schema(self) -> dict:
        return {
            "url": {"type": "str", "required": True, "description": "URL of web page to scrape"}
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {"task": "Extract article content", "call": {"url": "https://example.com/article"}},
            {
                "task": "Scrape documentation",
                "call": {"url": "https://docs.python.org/3/tutorial/"},
            },
            {"task": "Get blog post text", "call": {"url": "https://blog.example.com/post-title"}},
            {"task": "Extract news content", "call": {"url": "https://news.example.com/story"}},
        ]

    async def execute(self, url: str) -> Result[str, str]:
        """Execute clean web scraping."""
        if not url or not url.strip():
            return Err("URL cannot be empty")

        url = url.strip()

        if not validate_input(url):
            return Err("Invalid URL provided")

        try:
            import trafilatura
        except ImportError:
            return Err("Web scraping not available. Install with: pip install trafilatura")

        try:
            # Fetch and extract content
            content = trafilatura.fetch_url(url)
            if not content:
                return Err(f"Failed to fetch content from: {url}")

            extracted = trafilatura.extract(content, include_tables=True)
            if not extracted:
                return Err(f"No readable content found at: {url}")

            # Format with context
            formatted = self._format_content(extracted, url)
            return Ok(formatted)

        except Exception as e:
            return Err(f"Scraping failed: {str(e)}")

    def _format_content(self, content: str, url: str) -> str:
        """Format scraped content with clean structure."""
        if not content:
            return "No content extracted"

        # Get domain for context
        domain = self._extract_domain(url)

        # Clean whitespace
        cleaned = re.sub(r"\n\s*\n\s*\n", "\n\n", content.strip())
        word_count = len(cleaned.split())
        char_count = len(cleaned)

        # Header with context
        header = f"📄 Content from {domain} ({word_count:,} words)"

        # Handle long content intelligently
        if char_count > 10000:
            truncated = cleaned[:10000]
            return f"{header}\n\n{truncated}\n\n[Content truncated at 10,000 characters. Full length: {char_count:,} chars]"
        return f"{header}\n\n{cleaned}"

    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return "unknown-domain"
