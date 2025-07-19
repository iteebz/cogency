"""Query complexity analysis for adaptive reasoning depth."""


def analyze_query_complexity(user_input: str, tool_count: int) -> float:
    """
    Estimate query complexity for adaptive reasoning depth.
    
    Returns complexity score between 0.1 and 1.0 where:
    - 0.1-0.3: Simple queries (basic math, definitions)
    - 0.4-0.6: Moderate queries (information lookup, simple analysis)  
    - 0.7-0.9: Complex queries (multi-step reasoning, analysis)
    - 1.0: Maximum complexity (research, comprehensive analysis)
    """
    if not user_input:
        return 0.1
        
    # Base complexity from input length (longer = more complex)
    base = min(0.3, len(user_input) / 300)
    
    # Complexity keywords that indicate deeper reasoning needed
    complexity_keywords = [
        'analyze', 'compare', 'evaluate', 'research', 'investigate',
        'comprehensive', 'detailed', 'thorough', 'explain why',
        'implications', 'relationships', 'patterns', 'trends',
        'optimize', 'strategy', 'framework', 'methodology'
    ]
    
    keyword_matches = sum(1 for keyword in complexity_keywords 
                         if keyword in user_input.lower())
    keyword_score = min(0.4, keyword_matches * 0.1)
    
    # Tool availability indicates potential for complex workflows
    tool_score = min(0.3, tool_count / 15)
    
    # Question complexity indicators
    question_complexity = 0.0
    lower_input = user_input.lower()
    
    # Multi-part questions
    if any(word in lower_input for word in ['and then', 'also', 'additionally', 'furthermore']):
        question_complexity += 0.1
        
    # Conditional or hypothetical reasoning
    if any(word in lower_input for word in ['if', 'suppose', 'assume', 'what if', 'how would']):
        question_complexity += 0.1
        
    # Comparative analysis
    if any(word in lower_input for word in ['versus', 'vs', 'compared to', 'difference between']):
        question_complexity += 0.15
        
    # Time-sensitive or dynamic queries
    if any(word in lower_input for word in ['latest', 'recent', 'current', 'trending', 'update']):
        question_complexity += 0.05
    
    total_complexity = base + keyword_score + tool_score + question_complexity
    
    # Ensure bounds
    return max(0.1, min(1.0, total_complexity))


def get_complexity_category(complexity_score: float) -> str:
    """Get human-readable complexity category."""
    if complexity_score < 0.3:
        return "simple"
    elif complexity_score < 0.6:
        return "moderate" 
    elif complexity_score < 0.8:
        return "complex"
    else:
        return "highly_complex"


def estimate_iterations_needed(complexity_score: float, base_iterations: int = 5) -> int:
    """Estimate iterations needed based on complexity."""
    if complexity_score > 0.8:
        return min(base_iterations + 3, 8)
    elif complexity_score > 0.6:
        return min(base_iterations + 1, 6)
    elif complexity_score < 0.3:
        return max(base_iterations - 2, 2)
    else:
        return base_iterations