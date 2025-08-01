"""HTTP tool tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.tools.http import HTTP


@pytest.mark.asyncio
async def test_get():
    tool = HTTP()

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = Mock(return_value={"key": "value"})
        mock_response.url = "https://example.com"
        mock_response.elapsed.total_seconds = Mock(return_value=0.5)

        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

        result = await tool.run(url="https://example.com", method="get")
        assert result.success
        assert result.data["status_code"] == 200
        assert result.data["body"] == {"key": "value"}


@pytest.mark.asyncio
async def test_post():
    tool = HTTP()

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = Mock(return_value={"id": 123})
        mock_response.url = "https://example.com"
        mock_response.elapsed.total_seconds = Mock(return_value=0.3)

        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

        result = await tool.run(
            url="https://example.com", method="post", json_data={"name": "test"}
        )
        assert result.success
        assert result.data["status_code"] == 201


@pytest.mark.asyncio
async def test_text_response():
    tool = HTTP()

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<html>Hello</html>"
        mock_response.url = "https://example.com"
        mock_response.elapsed.total_seconds = Mock(return_value=0.2)

        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

        result = await tool.run(url="https://example.com")
        assert result.success
        assert result.data["body"] == "<html>Hello</html>"


@pytest.mark.asyncio
async def test_invalid_method():
    tool = HTTP()

    result = await tool.run(url="https://example.com", method="invalid")
    assert not result.success
    assert "Invalid HTTP method" in result.error


@pytest.mark.asyncio
async def test_get_with_json():
    tool = HTTP()

    result = await tool.run(url="https://example.com", method="get", json_data={"key": "value"})
    assert not result.success
    assert "GET requests cannot have json_data" in result.error


@pytest.mark.asyncio
async def test_timeout():
    tool = HTTP()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request.side_effect = Exception("Timeout")

        result = await tool.run(url="https://example.com")
        assert not result.success
        assert "HTTP request failed" in result.error


@pytest.mark.asyncio
async def test_all_methods():
    tool = HTTP()

    for method in ["get", "post", "put", "delete", "patch"]:
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = "OK"
            mock_response.url = "https://example.com"
            mock_response.elapsed.total_seconds = Mock(return_value=0.1)

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            json_data = {"data": "test"} if method != "get" else None
            result = await tool.run(url="https://example.com", method=method, json_data=json_data)
            assert result.success
