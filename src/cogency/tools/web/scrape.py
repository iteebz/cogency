"""Web scraping tool."""

import re
from urllib.parse import urlparse

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ..constants import SCRAPE_MAX_CHARS
from ..security import validate_input


class WebScrape(Tool):
    """Extract and format web content with clean output."""

    @property
    def name(self) -> str:
        return "scrape"

    @property
    def description(self) -> str:
        return "Extract web content"

    @property
    def schema(self) -> dict:
        return {"url": {}}

    async def execute(self, url: str, **kwargs) -> Result[ToolResult]:
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

            domain = self._extract_domain(url)

            content_formatted = self._format_content(extracted)
            size_kb = len(content_formatted) / 1024
            outcome = f"Content scraped from {domain} ({size_kb:.1f}KB)"
            return Ok(ToolResult(outcome, content_formatted))

        except Exception as e:
            return Err(f"Scraping failed: {str(e)}")

    def _format_content(self, content: str) -> str:
        """Content formatting."""
        if not content:
            return "No content extracted"

        # Clean whitespace intelligently - preserve structure
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", content.strip())

        # Handle length limits with intelligent truncation
        if len(cleaned) > SCRAPE_MAX_CHARS:
            # Find last complete sentence/paragraph before limit
            truncated = cleaned[:SCRAPE_MAX_CHARS]
            last_break = max(truncated.rfind("\n\n"), truncated.rfind(". "), truncated.rfind(".\n"))
            # Only break at sentence if we don't lose too much content
            if last_break > SCRAPE_MAX_CHARS * 0.8:
                truncated = truncated[: last_break + 1]

            return f"{truncated}\n\n[Content continues...]"

        return cleaned

    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return "unknown-domain"
