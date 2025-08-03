"""HTTP tool for API calls and web requests - FULL HTTP CLIENT."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class HTTPArgs:
    url: str
    method: str = "get"
    headers: Optional[Dict[str, str]] = None
    json_data: Optional[Dict[str, Any]] = None
    timeout: int = 30


@tool
class HTTP(Tool):
    """HTTP client for API calls, webhooks, and web requests with full verb support."""

    def __init__(self):
        super().__init__(
            name="http",
            description="Make HTTP requests (GET, POST, PUT, DELETE, PATCH) with JSON data support",
            schema="http(url=str, method='get'|'post'|'put'|'delete'|'patch', headers=dict, json_data=dict)",
            emoji="🌐",
            args=HTTPArgs,
            examples=[
                "http(url='https://api.example.com/data', method='get')",
                "http(url='https://api.example.com/users', method='post', json_data={'name': 'John'})",
                "http(url='https://api.example.com/user/123', method='put', json_data={'status': 'active'})",
            ],
            rules=[
                "Use GET for retrieving data.",
                "Use POST for creating resources.",
                "Use PUT for updating entire resources.",
                "Use PATCH for partial updates.",
                "Use DELETE for removing resources.",
                "GET requests must not include json_data.",
            ],
        )
        # Use base class formatting with templates
        self.param_key = "url"
        self.human_template = "Status: {status_code}"
        self.agent_template = "{method} {url} → {status_code}"

        # Supported HTTP methods
        self._methods = {"get", "post", "put", "delete", "patch"}

    async def run(
        self,
        url: str,
        method: str = "get",
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute HTTP request using dispatch pattern.
        Args:
            url: Target URL for the request
            method: HTTP method (get, post, put, delete, patch)
            headers: Optional HTTP headers dict
            json_data: Optional JSON data (automatically sets content-type)
            timeout: Request timeout in seconds (default: 30)
        Returns:
            Response data including status, headers, and body
        """
        method = method.lower()
        if method not in self._methods:
            available = ", ".join(self._methods)
            return Result.fail(f"Invalid HTTP method. Use: {available}")

        # GET requests cannot have json_data
        if method == "get" and json_data:
            return Result.fail("GET requests cannot have json_data")

        return await self._execute_request(method, url, headers, json_data, timeout)

    async def _execute_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict],
        json_data: Optional[Dict],
        timeout: int,
    ) -> Dict[str, Any]:
        """Execute HTTP request with unified error handling."""
        try:
            # Ensure URL has protocol
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            # Prepare request kwargs
            request_kwargs = {"timeout": timeout}
            # Handle headers
            if headers:
                request_kwargs["headers"] = headers
            # Handle json_data
            if json_data:
                request_kwargs["json"] = json_data
            # Execute request
            async with httpx.AsyncClient() as client:
                response = await client.request(method.upper(), url, **request_kwargs)
                # Try to parse response body
                try:
                    if response.headers.get("content-type", "").startswith("application/json"):
                        response_body = response.json()
                    else:
                        response_body = response.text
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Failed to decode JSON response, falling back to text. Error: {e}"
                    )
                    response_body = response.text
                return Result.ok(
                    {
                        "status_code": response.status_code,
                        "status": "success" if 200 <= response.status_code < 300 else "error",
                        "headers": dict(response.headers),
                        "body": response_body,
                        "url": str(response.url),
                        "method": method.upper(),
                        "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
                    }
                )
        except httpx.TimeoutException as e:
            logger.error(f"HTTP request timed out after {timeout} seconds: {e}")
            return Result.fail(f"Request timed out after {timeout} seconds")
        except httpx.ConnectError as e:
            error_str = str(e).lower()
            if "gaierror" in error_str or "nodename nor servname provided" in error_str:
                logger.error(f"DNS resolution failed for {url}: {e}")
                return Result.fail(f"Could not resolve domain: {url}")
            logger.error(f"HTTP connection failed to {url}: {e}")
            return Result.fail(f"Could not connect to {url}")
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return Result.fail(f"HTTP request failed: {str(e)}")
