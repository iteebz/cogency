"""Test Weather tool business logic."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.tools.weather import Weather
from cogency.utils.results import ToolResult


class TestWeather:
    """Test Weather tool business logic."""

    @pytest.mark.asyncio
    async def test_interface(self):
        """Weather tool implements required interface."""
        weather_tool = Weather()

        # Required attributes
        assert weather_tool.name == "weather"
        assert weather_tool.description
        assert hasattr(weather_tool, "run")

        # Schema and examples
        schema = weather_tool.schema
        examples = weather_tool.examples
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0

    @pytest.mark.asyncio
    async def test_invalid_city(self):
        """Weather tool handles invalid city."""
        weather_tool = Weather()

        # Mock httpx to return empty results for invalid city
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
