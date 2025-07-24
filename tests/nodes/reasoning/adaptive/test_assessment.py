"""Tests for tool assessment functionality."""

import pytest

from cogency.nodes.reasoning.adaptive.assessment import assess_tools
from cogency.utils.results import ExecutionResult


class TestToolQualityAssessment:
    """Test tool result quality assessment."""

    @pytest.mark.parametrize(
        "execution_results,expected_quality",
        [
            # Edge cases
            (None, "unknown"),  # Empty results
            (ExecutionResult(error="test"), "failed"),  # Failed execution
            (ExecutionResult(data={"results": []}), "poor"),  # No results
            # Quality assessment cases
            (
                ExecutionResult(
                    data={
                        "results": ["result1", "result2"],
                        "successful_count": 4,
                        "failed_count": 1,
                    }
                ),
                "good",
            ),  # Good quality
            (
                ExecutionResult(
                    data={
                        "results": ["result1"],
                        "successful_count": 3,
                        "failed_count": 2,
                    }
                ),
                "partial",
            ),  # Partial quality
            (
                ExecutionResult(
                    data={
                        "results": ["result1"],
                        "successful_count": 1,
                        "failed_count": 4,
                    }
                ),
                "poor",
            ),  # Poor quality
            (
                ExecutionResult(
                    data={
                        "results": ["result1"],
                        "successful_count": 0,
                        "failed_count": 0,
                    }
                ),
                "unknown",
            ),  # Unknown quality (zero total)
        ],
    )
    def test_quality_assessment(self, execution_results, expected_quality):
        """Test tool quality assessment with various execution results."""
        assert assess_tools(execution_results) == expected_quality
