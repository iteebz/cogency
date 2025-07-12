"""Tests for WebSearchTool."""

import time
from unittest.mock import patch, Mock

import pytest

from cogency.tools.web_search import WebSearchTool


class TestWebSearchTool:
    """Test suite for WebSearchTool."""

    def setup_method(self):
        """Setup test fixtures."""
        self.web_search = WebSearchTool()

    def test_web_search_initialization(self):
        """Test web search initialization."""
        assert self.web_search.name == "web_search"
        assert "DuckDuckGo" in self.web_search.description
        assert self.web_search._last_search_time == 0
        assert self.web_search._min_delay >= 0  # Should be positive

    def test_empty_query(self):
        """Test empty query handling."""
        result = self.web_search.run(query="")

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"
        assert result["tool"] == "web_search"

    def test_whitespace_query(self):
        """Test whitespace-only query handling."""
        result = self.web_search.run(query="   ")

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"

    def test_invalid_max_results(self):
        """Test invalid max_results parameter."""
        result = self.web_search.run(query="test", max_results=0)

        assert "error" in result
        assert result["error_code"] == "INVALID_MAX_RESULTS"
        assert "details" in result

    def test_negative_max_results(self):
        """Test negative max_results parameter."""
        result = self.web_search.run(query="test", max_results=-1)

        assert "error" in result
        assert result["error_code"] == "INVALID_MAX_RESULTS"

    def test_string_max_results(self):
        """Test string max_results parameter."""
        result = self.web_search.run(query="test", max_results="invalid")

        assert "error" in result
        assert result["error_code"] == "INVALID_MAX_RESULTS"

    @patch("cogency.tools.web_search.DDGS")
    def test_max_results_capping(self, mock_ddgs):
        """Test that max_results is capped at 10."""
        mock_ddgs.return_value.text.return_value = []

        self.web_search.run(query="test", max_results=15)

        # Should be called with max_results=10
        mock_ddgs.return_value.text.assert_called_with("test", max_results=10)

    @patch("cogency.tools.web_search.time.sleep")
    @patch("cogency.tools.web_search.time.time")
    def test_rate_limiting(self, mock_time, mock_sleep):
        """Test rate limiting functionality."""
        # Mock time to simulate rapid calls
        mock_time.side_effect = [0, 1.0, 1.5, 2.0]

        with patch("cogency.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.text.return_value = []

            # First call - should sleep full delay since last_search_time is 0
            self.web_search.run(query="test1")

            # Second call - should sleep remaining delay
            self.web_search.run(query="test2")

            # Should have slept twice
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(self.web_search._min_delay)  # First call

    @patch("cogency.tools.web_search.DDGS")
    def test_successful_search(self, mock_ddgs):
        """Test successful search with results."""
        mock_results = [
            {
                "title": "Test Title 1",
                "body": "Test snippet 1",
                "href": "https://example.com/1",
            },
            {
                "title": "Test Title 2", 
                "body": "Test snippet 2",
                "href": "https://example.com/2",
            },
        ]
        mock_ddgs.return_value.text.return_value = mock_results

        result = self.web_search.run(query="test query")

        assert result["success"] is True
        assert result["query"] == "test query"
        assert result["total_found"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Test Title 1"
        assert result["results"][0]["snippet"] == "Test snippet 1"
        assert result["results"][0]["url"] == "https://example.com/1"

    @patch("cogency.tools.web_search.DDGS")
    def test_no_results_found(self, mock_ddgs):
        """Test search with no results."""
        mock_ddgs.return_value.text.return_value = []

        result = self.web_search.run(query="nonexistent query")

        assert result["success"] is True
        assert result["query"] == "nonexistent query"
        assert result["total_found"] == 0
        assert result["results"] == []
        assert "No results found" in result["message"]

    @patch("cogency.tools.web_search.DDGS")
    def test_search_exception(self, mock_ddgs):
        """Test search exception handling."""
        mock_ddgs.return_value.text.side_effect = Exception("Network error")

        result = self.web_search.run(query="test")

        assert "error" in result
        assert result["error_code"] == "SEARCH_FAILED"
        assert "Network error" in result["error"]
        assert result["tool"] == "web_search"
        assert "details" in result

    @patch("cogency.tools.web_search.DDGS")
    def test_missing_result_fields(self, mock_ddgs):
        """Test handling of results with missing fields."""
        mock_results = [
            {
                "title": "Test Title",
                # Missing body and href
            }
        ]
        mock_ddgs.return_value.text.return_value = mock_results

        result = self.web_search.run(query="test")

        assert result["success"] is True
        assert result["results"][0]["title"] == "Test Title"
        assert result["results"][0]["snippet"] == "No snippet available"
        assert result["results"][0]["url"] == "No URL"

    def test_get_schema(self):
        """Test get_schema method."""
        schema = self.web_search.get_schema()

        assert "web_search" in schema
        assert "query=" in schema
        assert "max_results=" in schema

    def test_get_usage_examples(self):
        """Test get_usage_examples method."""
        examples = self.web_search.get_usage_examples()

        assert len(examples) > 0
        assert all("web_search(" in example for example in examples)
        assert any("query=" in example for example in examples)

    @patch("cogency.tools.web_search.DDGS")
    def test_validate_and_run_success(self, mock_ddgs):
        """Test successful validation and run."""
        mock_results = [{"title": "Test", "body": "Test", "href": "https://test.com"}]
        mock_ddgs.return_value.text.return_value = mock_results

        result = self.web_search.validate_and_run(query="test query")

        assert result["success"] is True
        assert result["total_found"] == len(mock_results)

    def test_validate_and_run_error(self):
        """Test error handling in validate_and_run."""
        result = self.web_search.validate_and_run(query="", max_results=-1)

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"

    @patch("cogency.tools.web_search.DDGS")
    def test_default_max_results(self, mock_ddgs):
        """Test default max_results from config."""
        mock_ddgs.return_value.text.return_value = []

        # Call without max_results parameter
        self.web_search.run(query="test")

        # Should use default from config or fallback
        call_args = mock_ddgs.return_value.text.call_args[1]
        assert "max_results" in call_args
        assert isinstance(call_args["max_results"], int)
        assert call_args["max_results"] > 0

    @patch("cogency.tools.web_search.DDGS")
    def test_large_result_set(self, mock_ddgs):
        """Test handling of large result sets."""
        # Create many mock results
        mock_results = [
            {
                "title": f"Title {i}",
                "body": f"Snippet {i}",
                "href": f"https://example{i}.com",
            }
            for i in range(20)
        ]
        mock_ddgs.return_value.text.return_value = mock_results

        result = self.web_search.run(query="popular topic", max_results=10)

        assert result["success"] is True
        assert result["total_found"] == 20  # All results returned by DDGS
        assert len(result["results"]) == 20

    @patch("cogency.tools.web_search.DDGS")
    def test_unicode_query(self, mock_ddgs):
        """Test search with unicode characters."""
        mock_results = [
            {
                "title": "Unicode Test 🌍",
                "body": "Unicode snippet with émojis",
                "href": "https://unicode.example.com",
            }
        ]
        mock_ddgs.return_value.text.return_value = mock_results

        result = self.web_search.run(query="search 世界 🔍")

        assert result["success"] is True
        assert result["query"] == "search 世界 🔍"
        assert result["results"][0]["title"] == "Unicode Test 🌍"