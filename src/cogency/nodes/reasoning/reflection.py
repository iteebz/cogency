"""Explicit reflection phases for deep mode - ultrathink style."""
from typing import Dict, Any, Optional


def get_reflection_prompt(
    tool_info: str,
    query: str,
    current_iteration: int,
    max_iterations: int,
    current_strategy: str,
    previous_attempts: str,
    last_tool_quality: str
) -> str:
    """Generate ultrathink-style reflection prompt for deep mode.
    
    REFLECTION → PLANNING → EXECUTION structure with explicit phases.
    """
    return f"""You are in DEEP REACT mode - use explicit reflection phases for sophisticated reasoning.

ORIGINAL QUERY: {query}
AVAILABLE TOOLS: {tool_info}

ITERATION: {current_iteration}/{max_iterations}
CURRENT STRATEGY: {current_strategy}
PREVIOUS ATTEMPTS: {previous_attempts}
LAST TOOL QUALITY: {last_tool_quality}

Follow this explicit reasoning structure:

🤔 REFLECTION PHASE:
What have I learned so far? What patterns do I see? What's working/not working?

📋 PLANNING PHASE: 
Based on my reflection, what's my next strategy? What specific approach should I take?
- Break down the problem if complex
- Identify key information needed  
- Plan tool usage sequence
- Consider potential obstacles

🎯 EXECUTION PHASE:
Now I'll take this specific action with clear reasoning.

COGNITIVE ADJUSTMENT: If this task is simpler than expected, you can downshift to fast mode.

Output JSON with structured reasoning:
{{
  "reflection": "What I've learned and observed so far",
  "planning": "My strategic approach for the next action", 
  "execution_reasoning": "Why I'm taking this specific action",
  "strategy": "approach_name",
  "switch_to": "fast" | null,
  "switch_reason": "why switching modes" | null
}}

Use tools if needed or provide direct response if you can answer completely."""


def get_reflection(llm_response: str) -> Dict[str, Optional[str]]:
    """Extract reflection phases from LLM response.
    
    Returns:
        Dict with reflection, planning, execution_reasoning phases
    """
    try:
        import json
        # Try to extract JSON from response
        start = llm_response.find('{')
        end = llm_response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = llm_response[start:end]
            data = json.loads(json_str)
            
            return {
                'reflection': data.get('reflection'),
                'planning': data.get('planning'),
                'execution_reasoning': data.get('execution_reasoning'),
                'strategy': data.get('strategy', 'unknown')
            }
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Fallback: try to extract phases from text
    reflection = None
    planning = None
    execution = None
    
    if "REFLECTION:" in llm_response or "🤔" in llm_response:
        # Try to extract reflection section
        lines = llm_response.split('\n')
        in_reflection = False
        reflection_lines = []
        
        for line in lines:
            if any(marker in line for marker in ["REFLECTION", "🤔"]):
                in_reflection = True
                continue
            elif any(marker in line for marker in ["PLANNING", "📋", "EXECUTION", "🎯"]):
                in_reflection = False
            elif in_reflection and line.strip():
                reflection_lines.append(line.strip())
        
        if reflection_lines:
            reflection = ' '.join(reflection_lines)
    
    return {
        'reflection': reflection,
        'planning': planning, 
        'execution_reasoning': execution,
        'strategy': 'extracted_from_text'
    }


def format_reflection(phases: Dict[str, Optional[str]]) -> str:
    """Format reflection phases for human-readable display.
    
    Args:
        phases: Dict with reflection phases
        
    Returns:
        Formatted string for streaming/display
    """
    parts = []
    
    if phases.get('reflection'):
        parts.append(f"🤔 REFLECTION: {phases['reflection']}")
    
    if phases.get('planning'):
        parts.append(f"📋 PLANNING: {phases['planning']}")
        
    if phases.get('execution_reasoning'):
        parts.append(f"🎯 EXECUTION: {phases['execution_reasoning']}")
    
    return '\n\n'.join(parts) if parts else "Thinking through the problem..."


def needs_reflection(react_mode: str, current_iteration: int = 0) -> bool:
    """Determine if explicit reflection should be used.
    
    Args:
        react_mode: Current react mode ('fast' or 'deep')
        current_iteration: Current iteration number
        
    Returns:
        True if reflection should be used
    """
    # Only use reflection in deep mode
    if react_mode != "deep":
        return False
        
    # Use reflection from the start in deep mode
    return True