from unittest.mock import patch

import pytest

from cogency.tools.base import BaseTool
from cogency.tools.calculator import CalculatorTool
from cogency.tools.web_search import WebSearchTool


class ConcreteTool(BaseTool):
    """Concrete implementation of BaseTool for testing."""

    def __init__(self):
        super().__init__(name="test_tool", description="A test tool")

    def run(self, **kwargs):
        if "error" in kwargs:
            raise ValueError("Test error")
        return {"result": "success", "args": kwargs}

    def get_schema(self):
        return "test_tool(arg1=str, arg2=int)"

    def get_usage_examples(self):
        return ["test_tool(arg1='hello', arg2=42)"]


class TestBaseTool:
    """Test suite for BaseTool abstract base class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tool = ConcreteTool()

    def test_base_tool_initialization(self):
        """Test BaseTool initialization."""
        assert self.tool.name == "test_tool"
        assert self.tool.description == "A test tool"

    def test_validate_and_run_success(self):
        """Test successful validation and run."""
        result = self.tool.validate_and_run(arg1="test", arg2=123)

        assert result["result"] == "success"
        assert result["args"]["arg1"] == "test"
        assert result["args"]["arg2"] == 123

    def test_validate_and_run_error(self):
        """Test error handling in validate_and_run."""
        result = self.tool.validate_and_run(error=True)

        assert "error" in result
        assert result["error"] == "Test error"

    def test_abstract_methods(self):
        """Test that abstract methods are implemented."""
        # These should not raise NotImplementedError
        self.tool.run()
        self.tool.get_schema()
        self.tool.get_usage_examples()

    def test_base_tool_cannot_be_instantiated(self):
        """Test that BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTool("test", "description")


class TestCalculatorTool:
    """Test suite for CalculatorTool."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = CalculatorTool()

    def test_calculator_initialization(self):
        """Test calculator initialization."""
        assert self.calculator.name == "calculator"
        assert "arithmetic" in self.calculator.description

    def test_addition(self):
        """Test addition operation."""
        result = self.calculator.run(operation="add", x1=2, x2=3)

        assert result["result"] == 5
        assert "error" not in result

    def test_subtraction(self):
        """Test subtraction operation."""
        result = self.calculator.run(operation="subtract", x1=10, x2=3)

        assert result["result"] == 7
        assert "error" not in result

    def test_multiplication(self):
        """Test multiplication operation."""
        result = self.calculator.run(operation="multiply", x1=4, x2=5)

        assert result["result"] == 20
        assert "error" not in result

    def test_division(self):
        """Test division operation."""
        result = self.calculator.run(operation="divide", x1=10, x2=2)

        assert result["result"] == 5.0
        assert "error" not in result

    def test_division_by_zero(self):
        """Test division by zero error."""
        result = self.calculator.run(operation="divide", x1=10, x2=0)

        assert "error" in result
        assert "divide by zero" in result["error"]

    def test_square_root(self):
        """Test square root operation."""
        result = self.calculator.run(operation="square_root", x1=9)

        assert result["result"] == 3.0
        assert "error" not in result

    def test_square_root_negative(self):
        """Test square root of negative number."""
        result = self.calculator.run(operation="square_root", x1=-4)

        assert "error" in result
        assert "negative number" in result["error"]

    def test_missing_parameters_add(self):
        """Test missing parameters for addition."""
        result = self.calculator.run(operation="add", x1=5)

        assert "error" in result
        assert "x1 and x2 are required" in result["error"]

    def test_missing_parameters_square_root(self):
        """Test missing parameters for square root."""
        result = self.calculator.run(operation="square_root")

        assert "error" in result
        assert "x1 is required" in result["error"]

    def test_unsupported_operation(self):
        """Test unsupported operation."""
        result = self.calculator.run(operation="power", x1=2, x2=3)

        assert "error" in result
        assert "Unsupported operation" in result["error"]

    def test_get_schema(self):
        """Test get_schema method."""
        schema = self.calculator.get_schema()

        assert "calculator" in schema
        assert "operation=" in schema
        assert "x1=" in schema
        assert "x2=" in schema

    def test_get_usage_examples(self):
        """Test get_usage_examples method."""
        examples = self.calculator.get_usage_examples()

        assert len(examples) > 0
        assert all("calculator(" in example for example in examples)
        assert any("add" in example for example in examples)
        assert any("multiply" in example for example in examples)
        assert any("square_root" in example for example in examples)

    def test_validate_and_run_success(self):
        """Test successful validation and run."""
        result = self.calculator.validate_and_run(operation="add", x1=2, x2=3)

        assert result["result"] == 5
        assert "error" not in result

    def test_validate_and_run_error(self):
        """Test error handling in validate_and_run."""
        result = self.calculator.validate_and_run(operation="divide", x1=10, x2=0)

        assert "error" in result
        assert "divide by zero" in result["error"]


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
        assert self.web_search._min_delay == 1.0

    def test_empty_query(self):
        """Test empty query handling."""
        result = self.web_search.run(query="")

        assert "error" in result
        assert "cannot be empty" in result["error"]

    def test_whitespace_query(self):
        """Test whitespace-only query handling."""
        result = self.web_search.run(query="   ")

        assert "error" in result
        assert "cannot be empty" in result["error"]

    def test_invalid_max_results(self):
        """Test invalid max_results parameter."""
        result = self.web_search.run(query="test", max_results=0)

        assert "error" in result
        assert "positive integer" in result["error"]

    def test_negative_max_results(self):
        """Test negative max_results parameter."""
        result = self.web_search.run(query="test", max_results=-1)

        assert "error" in result
        assert "positive integer" in result["error"]

    def test_max_results_capping(self):
        """Test that max_results is capped at 10."""
        with patch("cogency.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = []

            self.web_search.run(query="test", max_results=15)

            # Should be called with max_results=10
            mock_ddgs.return_value.__enter__.return_value.text.assert_called_with(
                "test", max_results=10
            )

    @patch("cogency.tools.web_search.time.sleep")
    @patch("cogency.tools.web_search.time.time")
    def test_rate_limiting(self, mock_time, mock_sleep):
        """Test rate limiting functionality."""
        # Mock time to simulate rapid calls
        # First call: current_time=0, last_search_time=0, time_since_last=0, sleep(1.0)
        # End of first call: time.time() = 1.0 (set last_search_time)
        # Second call: current_time=1.5, last_search_time=1.0, time_since_last=0.5, sleep(0.5)
        # End of second call: time.time() = 2.0
        mock_time.side_effect = [0, 1.0, 1.5, 2.0]

        with patch("cogency.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = []

            # First call - should sleep full delay since last_search_time is 0
            self.web_search.run(query="test1")

            # Second call - should sleep remaining delay
            self.web_search.run(query="test2")

            # Should have slept twice: once for 1.0 (first call) and once for 0.5 (second call)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1.0)  # First call
            mock_sleep.assert_any_call(0.5)  # Second call

    @patch("cogency.tools.web_search.DDGS")
    def test_successful_search(self, mock_ddgs):
        """Test successful search with results."""
        mock_results = [
            {"title": "Test Title 1", "body": "Test snippet 1", "href": "https://example.com/1"},
            {"title": "Test Title 2", "body": "Test snippet 2", "href": "https://example.com/2"},
        ]
        mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_results

        result = self.web_search.run(query="test query")

        assert "error" not in result
        assert result["query"] == "test query"
        assert result["total_found"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Test Title 1"
        assert result["results"][0]["snippet"] == "Test snippet 1"
        assert result["results"][0]["url"] == "https://example.com/1"

    @patch("cogency.tools.web_search.DDGS")
    def test_no_results_found(self, mock_ddgs):
        """Test search with no results."""
        mock_ddgs.return_value.__enter__.return_value.text.return_value = []

        result = self.web_search.run(query="nonexistent query")

        assert "error" not in result
        assert result["query"] == "nonexistent query"
        assert result["total_found"] == 0
        assert result["results"] == []
        assert "No results found" in result["message"]

    @patch("cogency.tools.web_search.DDGS")
    def test_search_exception(self, mock_ddgs):
        """Test search exception handling."""
        mock_ddgs.return_value.__enter__.return_value.text.side_effect = Exception("Network error")

        result = self.web_search.run(query="test")

        assert "error" in result
        assert "Search failed" in result["error"]
        assert "Network error" in result["error"]
        assert result["query"] == "test"
        assert result["total_found"] == 0

    @patch("cogency.tools.web_search.DDGS")
    def test_missing_result_fields(self, mock_ddgs):
        """Test handling of results with missing fields."""
        mock_results = [
            {
                "title": "Test Title",
                # Missing body and href
            }
        ]
        mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_results

        result = self.web_search.run(query="test")

        assert "error" not in result
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
        assert any("max_results=" in example for example in examples)

    @patch("cogency.tools.web_search.DDGS")
    def test_validate_and_run_success(self, mock_ddgs):
        """Test successful validation and run."""
        mock_results = [{"title": "Test", "body": "Test", "href": "https://test.com"}]
        mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_results

        result = self.web_search.validate_and_run(query="test query")

        assert "error" not in result
        assert result["total_found"] == 1

    def test_validate_and_run_error(self):
        """Test error handling in validate_and_run."""
        result = self.web_search.validate_and_run(query="", max_results=-1)

        assert "error" in result
        assert "cannot be empty" in result["error"]
