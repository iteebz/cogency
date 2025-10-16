import re
from urllib.parse import urlparse

from ..core.protocols import Tool, ToolResult
from ..core.security import safe_execute
from ..lib.logger import logger

SCRAPE_LIMIT = 3000


class Scrape(Tool):
    """Scrape webpage."""

    name = "scrape"
    description = "Scrape webpage. Extracts readable text, 3KB limit."
    schema = {"url": {}}

    def describe(self, args: dict) -> str:
        return f"Scraping {args.get('url', 'url')}"

    @safe_execute
    async def execute(self, url: str, **kwargs) -> ToolResult:
        if not url or not url.strip():
            return ToolResult(outcome="URL cannot be empty", error=True)

        url = url.strip()

        try:
            import trafilatura
        except ImportError:
            return ToolResult(
                outcome="Web scraping not available. Install with: pip install trafilatura",
                error=True,
            )

        # Fetch and extract content
        content = trafilatura.fetch_url(url)
        if not content:
            return ToolResult(outcome=f"Failed to fetch content from: {url}", error=True)

        domain = self._extract_domain(url)

        extracted = trafilatura.extract(content, include_tables=True)
        if not extracted:
            return ToolResult(
                outcome=f"Scraped {domain} (0KB)", content="No readable content found"
            )

        content_formatted = self._format_content(extracted)
        size_kb = len(content_formatted) / 1024

        outcome = f"Scraped {domain} ({size_kb:.1f}KB)"
        return ToolResult(outcome=outcome, content=content_formatted)

    def _format_content(self, content: str) -> str:
        if not content:
            return "No content extracted"

        # Clean whitespace intelligently - preserve structure
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", content.strip())

        # Handle length limits with intelligent truncation
        if len(cleaned) > SCRAPE_LIMIT:
            # Find last complete sentence/paragraph before limit
            truncated = cleaned[:SCRAPE_LIMIT]
            last_break = max(truncated.rfind("\n\n"), truncated.rfind(". "), truncated.rfind(".\n"))
            # Only break at sentence if we don't lose too much content
            if last_break > SCRAPE_LIMIT * 0.8:
                truncated = truncated[: last_break + 1]

            return f"{truncated}\n\n[Content continues...]"

        return cleaned

    def _extract_domain(self, url: str) -> str:
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"Domain extraction failed for {url}: {e}")
            return "unknown-domain"
