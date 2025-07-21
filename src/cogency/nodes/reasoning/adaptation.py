"""Bidirectional mode switching logic - the core innovation."""
from typing import Dict, Any, Optional, Tuple
import json


def extract_mode_switch(llm_response: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract mode switching from LLM response.
    
    Returns:
        (switch_to, switch_reason) or (None, None) if no switch requested
    """
    try:
        # Try to extract JSON from response
        start = llm_response.find('{')
        end = llm_response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = llm_response[start:end]
            data = json.loads(json_str)
            
            # Handle both escalate_to (old) and switch_to (new) formats
            switch_to = data.get('switch_to') or data.get('escalate_to')
            switch_reason = data.get('switch_reason') or data.get('escalation_reason')
            
            return switch_to, switch_reason
    except (json.JSONDecodeError, ValueError):
        pass
    
    return None, None


def should_switch_modes(
    current_mode: str, 
    switch_to: Optional[str], 
    switch_reason: Optional[str],
    current_iteration: int = 0
) -> bool:
    """Determine if mode switch should be executed.
    
    Args:
        current_mode: Current react mode ('fast' or 'deep')
        switch_to: Requested switch mode ('fast' or 'deep')
        switch_reason: Reason for switching
        current_iteration: Current iteration (prevent early/late switching)
    
    Returns:
        True if switch should be executed
    """
    if not switch_to or not switch_reason:
        return False
        
    # Must be different from current mode
    if switch_to == current_mode:
        return False
        
    # Only allow valid mode transitions
    if switch_to not in ['fast', 'deep']:
        return False
        
    # Prevent switching too early (let mode try at least once)
    if current_iteration < 1:
        return False
        
    # Prevent switching too late (close to max iterations)
    if current_iteration >= 4:
        return False
        
    return True


def execute_mode_switch(
    state: Dict[str, Any], 
    new_mode: str, 
    switch_reason: str
) -> Dict[str, Any]:
    """Execute bidirectional mode switch with context preservation.
    
    Args:
        state: Current agent state
        new_mode: Target mode ('fast' or 'deep')  
        switch_reason: Reason for switching
        
    Returns:
        Updated state with new mode and preserved context
    """
    # Update react mode
    state['react_mode'] = new_mode
    
    # Preserve cognitive state but update mode-specific limits
    if 'cognitive_state' in state:
        cognitive_state = state['cognitive_state']
        cognitive_state['react_mode'] = new_mode
        
        # Adjust memory limits for new mode
        if new_mode == 'fast':
            cognitive_state['max_history'] = 3
            cognitive_state['max_failures'] = 5
        else:  # deep
            cognitive_state['max_history'] = 10
            cognitive_state['max_failures'] = 15
    
    # Track mode switch for tracing
    mode_switches = state.get('mode_switches', [])
    mode_switches.append({
        'from_mode': state.get('previous_react_mode', 'unknown'),
        'to_mode': new_mode,
        'reason': switch_reason,
        'iteration': state.get('current_iteration', 0)
    })
    state['mode_switches'] = mode_switches
    state['previous_react_mode'] = state.get('react_mode', 'unknown')
    
    return state


def get_mode_switch_prompt_addition(current_mode: str) -> str:
    """Get prompt addition for bidirectional mode switching.
    
    Args:
        current_mode: Current react mode ('fast' or 'deep')
        
    Returns:
        Prompt text for mode switching capability
    """
    if current_mode == 'deep':
        return """
COGNITIVE ADJUSTMENT: If this task is simpler than expected, you can downshift to fast mode.

Output JSON with mode switching:
{
  "reasoning": "your analysis",
  "strategy": "approach_name", 
  "switch_to": "fast" | null,
  "switch_reason": "why switching modes" | null
}"""
    else:  # fast
        return """
COGNITIVE ADJUSTMENT: If this needs deeper analysis, complex synthesis, or multi-step reasoning, escalate to deep mode.

Output JSON with escalation:
{
  "reasoning": "brief thought",
  "strategy": "direct_approach",
  "switch_to": "deep" | null,
  "switch_reason": "why switching modes" | null
}"""