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
    body: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, str]] = None
    timeout: int = 30


@tool
class HTTP(Tool):
    """HTTP client for API calls, webhooks, and web requests with full verb support."""

    # Custom formatting for HTTP requests
    human_template = "Status: {status_code}"
    agent_template = "{method} {url} → {status_code}"
    param_key = "url"

    def __init__(self):
        super().__init__(
            name="http",
            description="Make HTTP requests (GET, POST, PUT, DELETE, PATCH) with headers, auth, and body support",
            schema="http(url=str, method='get'|'post'|'put'|'delete'|'patch', headers=dict, body=str, json_data=dict)",
            emoji="🌐",
            params=HTTPArgs,
            examples=[
                "http(url='https://api.example.com/data', method='get')",
                "http(url='https://api.example.com/users', method='post', json_data={'name': 'John'})",
                "http(url='https://api.example.com/user/123', method='put', auth={'type': 'bearer', 'token': 'xyz'})",
            ],
            rules=[
                "Use GET for retrieving data.",
                "Use POST for creating resources.",
                "Use PUT for updating entire resources.",
                "Use PATCH for partial updates.",
                "Use DELETE for removing resources.",
                "GET requests must not include 'body' or 'json_data'.",
                "Provide either 'body' (string) or 'json_data' (dict), but not both.",
            ],
        )

        # Beautiful dispatch pattern - extensible and clean
        self._methods = {
            "get": self._get,
            "post": self._post,
            "put": self._put,
            "delete": self._delete,
            "patch": self._patch,
        }

    async def run(
        self,
        url: str,
        method: str = "get",
        headers: Optional[Dict] = None,
        body: Optional[str] = None,
        json_data: Optional[Dict] = None,
        auth: Optional[Dict] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute HTTP request using dispatch pattern.
        Args:
            url: Target URL for the request
            method: HTTP method (get, post, put, delete, patch)
            headers: Optional HTTP headers dict
            body: Optional request body as string
            json_data: Optional JSON data (automatically sets content-type)
            auth: Optional auth dict with 'type' and credentials
            timeout: Request timeout in seconds (default: 30)
        Returns:
            Response data including status, headers, and body
        """
        method = method.lower()
        if method not in self._methods:
            available = ", ".join(self._methods.keys())
            return Result.fail(f"Invalid HTTP method. Use: {available}")
        # Dispatch to appropriate method
        method_func = self._methods[method]
        return await method_func(url, headers, body, json_data, auth, timeout)

    async def _execute_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict],
        body: Optional[str],
        json_data: Optional[Dict],
        auth: Optional[Dict],
        timeout: int,
    ) -> Dict[str, Any]:
        """Execute HTTP request with unified error handling."""
        try:
            # Prepare request kwargs
            request_kwargs = {"timeout": timeout}
            # Handle headers
            if headers:
                request_kwargs["headers"] = headers
            # Handle body vs json_data
            if json_data:
                request_kwargs["json"] = json_data
            elif body:
                request_kwargs["content"] = body
            # Handle authentication
            if auth:
                auth_type = auth.get("type", "").lower()
                if auth_type == "bearer":
                    token = auth.get("token")
                    if not token:
                        return Result.fail("Bearer token required for bearer auth")
                    request_kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {token}"
                elif auth_type == "basic":
                    username = auth.get("username")
                    password = auth.get("password")
                    if not username or not password:
                        return Result.fail("Username and password required for basic auth")
                    request_kwargs["auth"] = (username, password)
                elif auth_type == "api_key":
                    key = auth.get("key")
                    header = auth.get("header", "X-API-Key")
                    if not key:
                        return Result.fail("API key required for api_key auth")
                    request_kwargs.setdefault("headers", {})[header] = key
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
                        "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
                    }
                )
        except httpx.TimeoutException as e:
            logger.error(f"HTTP request timed out after {timeout} seconds: {e}")
            return Result.fail(f"Request timed out after {timeout} seconds")
        except httpx.ConnectError as e:
            logger.error(f"HTTP connection failed to {url}: {e}")
            return Result.fail(f"Could not connect to {url}")
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return Result.fail(f"HTTP request failed: {str(e)}")

    async def _get(
        self,
        url: str,
        headers: Optional[Dict],
        body: Optional[str],
        json_data: Optional[Dict],
        auth: Optional[Dict],
        timeout: int,
    ) -> Dict[str, Any]:
        """GET request."""
        if body or json_data:
            return Result.fail("GET requests cannot have a body")
        return await self._execute_request("get", url, headers, None, None, auth, timeout)

    async def _post(
        self,
        url: str,
        headers: Optional[Dict],
        body: Optional[str],
        json_data: Optional[Dict],
        auth: Optional[Dict],
        timeout: int,
    ) -> Dict[str, Any]:
        """POST request."""
        return await self._execute_request("post", url, headers, body, json_data, auth, timeout)

    async def _put(
        self,
        url: str,
        headers: Optional[Dict],
        body: Optional[str],
        json_data: Optional[Dict],
        auth: Optional[Dict],
        timeout: int,
    ) -> Dict[str, Any]:
        """PUT request."""
        return await self._execute_request("put", url, headers, body, json_data, auth, timeout)

    async def _delete(
        self,
        url: str,
        headers: Optional[Dict],
        body: Optional[str],
        json_data: Optional[Dict],
        auth: Optional[Dict],
        timeout: int,
    ) -> Dict[str, Any]:
        """DELETE request."""
        return await self._execute_request("delete", url, headers, body, json_data, auth, timeout)

    async def _patch(
        self,
        url: str,
        headers: Optional[Dict],
        body: Optional[str],
        json_data: Optional[Dict],
        auth: Optional[Dict],
        timeout: int,
    ) -> Dict[str, Any]:
        """PATCH request."""
        return await self._execute_request("patch", url, headers, body, json_data, auth, timeout)
