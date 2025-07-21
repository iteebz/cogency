"""Web content extraction tool using trafilatura."""
import logging
from typing import Any, Dict, List

import trafilatura

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
            emoji="📖"
        )

    async def run(self, url: str, favor_precision: bool = True, **kwargs) -> Dict[str, Any]:
        """Extract clean content from a web page.
        
        Args:
            url: URL to scrape content from
            favor_precision: Prioritize precision over recall in extraction
            
        Returns:
            Dict with extracted content, metadata, and status
        """
        if not url or not isinstance(url, str):
            return {
                "success": False,
                "error": "URL parameter is required and must be a string",
                "content": None
            }

        try:
            # Fetch URL content first
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {
                    "success": False,
                    "error": f"Could not fetch content from {url}",
                    "content": None,
                    "url": url
                }
            
            # Extract content with options for cleanest output
            content = trafilatura.extract(
                downloaded,
                favor_precision=favor_precision,
                include_comments=False,
                include_tables=False,
                no_fallback=True
            )
            
            if content:
                # Also extract metadata
                metadata = trafilatura.extract_metadata(downloaded)
                
                return {
                    "success": True,
                    "content": content.strip(),
                    "metadata": {
                        "title": metadata.title if metadata and metadata.title else None,
                        "author": metadata.author if metadata and metadata.author else None,
                        "date": metadata.date if metadata and metadata.date else None,
                        "url": metadata.url if metadata and metadata.url else url
                    },
                    "url": url
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not extract content from {url}",
                    "content": None,
                    "url": url
                }
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "success": False,
                "error": f"Scraping failed: {str(e)}",
                "content": None,
                "url": url
            }

    def get_schema(self) -> str:
        """Return tool call schema for LLM formatting."""
        return """scrape(url="https://example.com", favor_precision=True)"""

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls for LLM guidance."""
        return [
            'scrape(url="https://news.ycombinator.com/item?id=12345")',
            'scrape(url="https://blog.example.com/article", favor_precision=False)',
            'scrape(url="https://en.wikipedia.org/wiki/Machine_learning")'
        ]