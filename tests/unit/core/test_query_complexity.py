#!/usr/bin/env python3
"""Tests for query complexity estimation."""

import asyncio
from cogency.nodes.react_loop import _complexity_score


class TestQueryComplexityEstimation:
    """Tests for query complexity estimation."""
    
    def test_simple_query_complexity(self):
        """Test complexity estimation for simple queries."""
        simple_queries = [
            "What is Python?",
            "When was Python created?",
            "Who created Python?",
            "Define machine learning"
        ]
        
        for query in simple_queries:
            complexity = _complexity_score(query, 5)
            assert 0.1 <= complexity <= 0.5, f"Simple query '{query}' should have low complexity, got {complexity}"
    
    def test_complex_query_complexity(self):
        """Test complexity estimation for complex queries."""
        complex_queries = [
            "Analyze the performance implications of different machine learning frameworks and compare their trade-offs",
            "Research and evaluate the comprehensive security implications of implementing microservices architecture",
            "Investigate the detailed performance characteristics of various database engines and provide recommendations"
        ]
        
        for query in complex_queries:
            complexity = _complexity_score(query, 10)
            assert 0.5 <= complexity <= 1.0, f"Complex query '{query}' should have high complexity, got {complexity}"
    
    def test_tool_count_influence(self):
        """Test that tool count influences complexity estimation."""
        query = "Analyze the system performance"
        
        low_tool_complexity = _complexity_score(query, 2)
        high_tool_complexity = _complexity_score(query, 20)
        
        assert high_tool_complexity > low_tool_complexity, "More tools should increase complexity"
    
    def test_complexity_bounds(self):
        """Test that complexity is always bounded between 0.1 and 1.0."""
        test_cases = [
            ("", 0),  # Empty query, no tools
            ("What?", 1),  # Minimal query
            ("x" * 1000, 100)  # Very long query with many tools
        ]
        
        for query, tool_count in test_cases:
            complexity = _complexity_score(query, tool_count)
            assert 0.1 <= complexity <= 1.0, f"Complexity {complexity} should be bounded for query length {len(query)}"


