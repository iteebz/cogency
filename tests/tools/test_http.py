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
        schema = http.schema
        examples = http.examples
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
