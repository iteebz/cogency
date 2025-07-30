"""Web content extraction tool using trafilatura."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import trafilatura
from resilient_result import Result
from trafilatura.settings import use_config

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)

# Configure trafilatura with conservative timeouts and size limits
config = use_config()
config.set("DEFAULT", "DOWNLOAD_TIMEOUT", "5")  # 5 second timeout
config.set("DEFAULT", "MAX_FILE_SIZE", "512000")  # 500KB max file size


@dataclass
class ScrapeArgs:
    url: str
    favor_precision: bool = True


@tool
class Scrape(Tool):
    """Extract clean text content from web pages using trafilatura."""

    def __init__(self):
        super().__init__(
            name="scrape",
            description="Extract clean text content from web pages, removing ads, navigation, and formatting",
            schema="scrape(url: str, favor_precision: bool = True)",
            emoji="📖",
            params=ScrapeArgs,
            examples=[
                "scrape(url='https://example.com/article')",
                "scrape(url='https://news.site.com/story', favor_precision=True)",
                "scrape(url='https://blog.com/post', favor_precision=False)",
            ],
            rules=[
                "Provide a valid and accessible URL.",
                "Avoid re-scraping URLs that previously failed or returned no content.",
                "If a URL fails to scrape, try alternative sources instead of retrying.",
                "Large content will be automatically truncated to prevent timeouts.",
            ],
        )

    async def run(self, url: str, favor_precision: bool = True, **kwargs) -> Dict[str, Any]:
        """Extract clean content from a web page."""
        try:
            # Fetch URL content with timeout and size limits
            downloaded = trafilatura.fetch_url(url, config=config)
            if not downloaded:
                return Result.fail(f"Could not fetch content from {url}")

            # Check content size before processing
            if len(downloaded) > 512000:  # 500KB limit
                return Result.fail(f"Content too large ({len(downloaded)} bytes) from {url}")

            # Extract content with options for cleanest output
            content = trafilatura.extract(
                downloaded,
                favor_precision=favor_precision,
                include_comments=False,
                include_tables=False,
                no_fallback=True,
                config=config,
            )
            if content:
                # Limit content size for agent processing
                if len(content) > 10000:  # 10KB limit for agent context
                    content = content[:10000] + "\n\n[Content truncated due to size limit]"

                # Also extract metadata
                metadata = trafilatura.extract_metadata(downloaded)
                return Result.ok(
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
                return Result.fail(f"Could not extract content from {url}")
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return Result.fail(f"Scraping failed: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format scrape execution for display."""
        from urllib.parse import urlparse

        from cogency.utils import truncate

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

        # Format results - results is now the Result.data
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
