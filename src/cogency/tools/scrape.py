import logging
import re
from dataclasses import dataclass
from typing import Annotated, Any
from urllib.parse import urlparse

from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import safe_execute
from cogency.core.tool import tool

logger = logging.getLogger(__name__)

SCRAPE_LIMIT = 3000


@dataclass
class ScrapeParams:
    url: Annotated[str, ToolParam(description="URL to scrape")]


def _format_content(content: str) -> str:
    if not content:
        return "No content extracted"

    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", content.strip())

    if len(cleaned) > SCRAPE_LIMIT:
        truncated = cleaned[:SCRAPE_LIMIT]
        last_break = max(truncated.rfind("\n\n"), truncated.rfind(". "), truncated.rfind(".\n"))
        if last_break > SCRAPE_LIMIT * 0.8:
            truncated = truncated[: last_break + 1]

        return f"{truncated}\n\n[Content continues...]"

    return cleaned


def _extract_domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
        return domain.removeprefix("www.")
    except Exception as e:
        logger.warning(f"Domain extraction failed for {url}: {e}")
        return "unknown-domain"


@tool("Scrape webpage. Extracts readable text (3KB limit).")
@safe_execute
async def Scrape(
    params: ScrapeParams,
    **kwargs: Any,
) -> ToolResult:
    if not params.url or not params.url.strip():
        return ToolResult(outcome="URL cannot be empty", error=True)

    url = params.url.strip()

    try:
        import trafilatura
    except ImportError:
        return ToolResult(
            outcome="Web scraping not available. Install with: pip install trafilatura",
            error=True,
        )

    content = trafilatura.fetch_url(url)
    if not content:
        return ToolResult(outcome=f"Failed to fetch content from: {url}", error=True)

    domain = _extract_domain(url)

    extracted = trafilatura.extract(content, include_tables=True)
    if not extracted:
        return ToolResult(outcome=f"Scraped {domain} (0KB)", content="No readable content found")

    content_formatted = _format_content(extracted)
    size_kb = len(content_formatted) / 1024

    outcome = f"Scraped {domain} ({size_kb:.1f}KB)"
    return ToolResult(outcome=outcome, content=content_formatted)
