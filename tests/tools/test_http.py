"""Test HTTP tool business logic."""

import pytest

from cogency.tools.http import HTTP


class TestHTTP:
    """Test HTTP tool business logic."""

    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """HTTP tool implements required interface."""
        http = HTTP()

        # Required attributes
        assert http.name == "http"
        assert http.description
        assert hasattr(http, "run")

        # Schema and examples
        schema = http.schema()
        examples = http.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0

    @pytest.mark.asyncio
    async def test_invalid_method(self):
        """HTTP tool handles invalid methods."""
        http = HTTP()

        result = await http.run(url="https://httpbin.org/get", method="invalid")
        assert "error" in result
        assert "Invalid HTTP method" in result["error"]

    @pytest.mark.asyncio
    async def test_get_with_body_error(self):
        """GET requests cannot have body."""
        http = HTTP()

        result = await http.run(url="https://httpbin.org/get", method="get", body="test")
        assert "error" in result
        assert "GET requests cannot have a body" in result["error"]
