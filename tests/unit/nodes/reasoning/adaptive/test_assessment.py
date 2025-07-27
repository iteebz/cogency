"""Tests for tool assessment functionality."""

import pytest
from resilient_result import Result

from cogency.nodes.reasoning.adaptive.assessment import assess_tools


class TestToolQualityAssessment:
    """Test tool result quality assessment."""

    @pytest.mark.parametrize(
        "execution_results,expected_quality",
        [
            # Edge cases
            (None, "unknown"),  # Empty results
            (Result(error="test"), "failed"),  # Failed execution
            (Result(data={"results": []}), "poor"),  # No results
            # Quality assessment cases
            (
                Result(
                    data={
                        "results": ["result1", "result2"],
                        "successful_count": 4,
                        "failed_count": 1,
                    }
                ),
                "good",
            ),  # Good quality
            (
                Result(
                    data={
                        "results": ["result1"],
                        "successful_count": 3,
                        "failed_count": 2,
                    }
                ),
                "partial",
            ),  # Partial quality
            (
                Result(
                    data={
                        "results": ["result1"],
                        "successful_count": 1,
                        "failed_count": 4,
                    }
                ),
                "poor",
            ),  # Poor quality
            (
                Result(
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
