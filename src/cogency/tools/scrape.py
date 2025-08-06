"""Web content extraction tool using trafilatura."""

import logging
from dataclasses import dataclass
from typing import Any, Dict

import trafilatura
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class ScrapeArgs:
    url: str


@tool
class Scrape(Tool):
    """Extract text content from web pages using trafilatura."""

    def __init__(self):
        super().__init__(
            name="scrape",
            description="Extract clean text content from web pages, removing ads, navigation, and formatting",
            schema="scrape(url: str)",
            emoji="📖",
            args=ScrapeArgs,
            examples=[
                '{"name": "scrape", "args": {"url": "https://example.com/article"}}',
                '{"name": "scrape", "args": {"url": "https://news.site.com/story"}}',
                '{"name": "scrape", "args": {"url": "https://blog.com/post"}}',
            ],
            rules=[
                'CRITICAL: Use JSON format: {"name": "scrape", "args": {"url": "..."}}. Never use function-call syntax.',
                "Provide a valid and accessible URL.",
                "Avoid re-scraping URLs that previously failed or returned no content.",
                "If a URL fails to scrape, try alternative sources instead of retrying.",
            ],
        )
        # Use base class formatting with templates
        self.arg_key = "url"
        self.human_template = "Scraped '{title}'"
        self.agent_template = "scrape {url} → {title}"

    async def run(self, url: str, **kwargs) -> Dict[str, Any]:
        """Extract content from a web page."""
        try:
            # Fetch URL content
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return Result.fail(f"Could not fetch content from {url}")

            # Extract content with default settings
            content = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if content:
                # Extract metadata
                metadata = trafilatura.extract_metadata(downloaded)
                title = metadata.title if metadata and metadata.title else "Untitled"

                return Result.ok(
                    {
                        "content": content.strip(),
                        "title": title,
                        "url": url,
                    }
                )
            else:
                return Result.fail(f"Could not extract content from {url}")
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return Result.fail(f"Scraping failed: {str(e)}")
