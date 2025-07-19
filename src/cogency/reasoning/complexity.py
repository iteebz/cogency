"""Query complexity analysis for adaptive reasoning depth."""


def analyze_query_complexity(user_input: str, tool_count: int) -> float:
    """Simple heuristic complexity analysis - NO NESTED LLM CALLS."""
    if not user_input:
        return 0.1
    
    # Length-based scoring
    complexity = min(0.4, len(user_input) / 200)
    
    # Tool availability factor
    complexity += min(0.2, tool_count / 20)
    
    # Question complexity indicators
    complexity += min(0.2, user_input.count('?') * 0.1)
    complexity += min(0.2, user_input.count(' and ') * 0.1)
    
    return max(0.1, min(1.0, complexity))


