"""Test Weather tool business logic."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.tools.weather import Weather


@pytest.mark.asyncio
async def test_interface():
    weather_tool = Weather()

    assert weather_tool.name == "weather"
    assert weather_tool.description
    assert hasattr(weather_tool, "run")

    schema = weather_tool.schema
    examples = weather_tool.examples
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    assert "city" in schema["properties"]
    assert isinstance(examples, list) and len(examples) > 0


@pytest.mark.asyncio
async def test_invalid():
    weather_tool = Weather()

    mock_response = Mock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_async_client.return_value.__aenter__.return_value = mock_client

        result = await weather_tool.run(city="ThisIsNotARealLocationXYZ123")
        assert not result.success
        assert "not found" in result.error
