"""HTTP tool business logic tests."""

import pytest

from cogency.tools.http import HTTP


@pytest.mark.asyncio
async def test_basic_interface():
    http = HTTP()

    assert http.name == "http"
    assert http.description
    assert hasattr(http, "run")

    schema = http.schema
    examples = http.examples
    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0
