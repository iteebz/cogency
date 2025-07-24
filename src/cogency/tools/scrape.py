"""Web content extraction tool using trafilatura."""

import logging
from typing import Any, Dict, Optional

import trafilatura

from cogency.utils.results import ToolResult

from .base import BaseTool
from .registry import tool

logger = logging.getLogger(__name__)


@tool
class Scrape(BaseTool):
    """Extract clean text content from web pages using trafilatura."""

    def __init__(self):
        super().__init__(
            name="scrape",
            description="Extract clean text content from web pages, removing ads, navigation, and formatting",
            emoji="📖",
            schema="scrape(url='string', favor_precision=bool)",
            examples=[
                "scrape(url='https://example.com/article')",
                "scrape(url='https://news.site.com/story', favor_precision=True)",
                "scrape(url='https://blog.com/post', favor_precision=False)",
            ],
            rules=[
                "Provide a valid and accessible URL.",
            ],
        )

    async def run(self, url: str, favor_precision: bool = True, **kwargs) -> Dict[str, Any]:
        """Extract clean content from a web page."""
        if not url or not isinstance(url, str):
            return ToolResult.fail("URL parameter is required and must be a string")
        try:
            # Fetch URL content first
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return ToolResult.fail(f"Could not fetch content from {url}")
            # Extract content with options for cleanest output
            content = trafilatura.extract(
                downloaded,
                favor_precision=favor_precision,
                include_comments=False,
                include_tables=False,
                no_fallback=True,
            )
            if content:
                # Also extract metadata
                metadata = trafilatura.extract_metadata(downloaded)
                return ToolResult.ok(
                    {
                        "content": content.strip(),
                        "metadata": {
                            "title": metadata.title if metadata and metadata.title else None,
                            "author": metadata.author if metadata and metadata.author else None,
                            "date": metadata.date if metadata and metadata.date else None,
                            "url": metadata.url if metadata and metadata.url else url,
                        },
                        "url": url,
                    }
                )
            else:
                return ToolResult.fail(f"Could not extract content from {url}")
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ToolResult.fail(f"Scraping failed: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[ToolResult] = None
    ) -> tuple[str, str]:
        """Format scrape execution for display."""
        from urllib.parse import urlparse

        from cogency.utils.formatting import truncate

        url = params.get("url", "")
        if url:
            # Extract domain name for cleaner display
            try:
                domain = urlparse(url).netloc
                param_str = f"({domain})"
            except Exception as e:
                logger.warning(f"Failed to parse URL {url} for formatting: {e}")
                param_str = f"({truncate(url, 50)})"
        else:
            param_str = ""

        if results is None:
            return param_str, ""

        # Format results - results is now the ToolResult.data
        if results.failure:
            result_str = f"Error: {results.error}"
        else:
            data = results.data
            content = data.get("content", "")
            metadata = data.get("metadata", {})
            title = metadata.get("title", "Untitled")
            if content:
                content_preview = content[:100] + "..." if len(content) > 100 else content
                result_str = f"Scraped '{title}': {content_preview}"
            else:
                result_str = f"Scraped '{title}' (no content extracted)"
        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format scrape results for agent action history."""
        if not result_data:
            return "No result"

        content = result_data.get("content", "")
        metadata = result_data.get("metadata", {})
        url = result_data.get("url", "")
        title = metadata.get("title", "Untitled")

        if content:
            content_preview = content[:100] + "..." if len(content) > 100 else content
            return f"Scraped '{title}' from {url}: {content_preview}"
        else:
            return f"Scraped {url} (no content extracted)"
