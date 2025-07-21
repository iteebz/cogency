"""LLM-based memory relevance scoring - pure semantic approach without heuristic approximations."""
from typing import Dict, Any, List, Optional
import json


def score_memory_relevance(
    current_query: str,
    memory_items: List[Dict[str, Any]],
    llm_client,
    max_items: int = 10
) -> List[Dict[str, Any]]:
    """Score memory items for relevance using LLM semantic understanding.
    
    Args:
        current_query: The current user query/task
        memory_items: List of memory items to score
        llm_client: LLM client for scoring
        max_items: Maximum items to return
        
    Returns:
        List of memory items sorted by relevance (highest first)
    """
    if not memory_items or not current_query.strip():
        return memory_items[:max_items]
    
    # Prepare items for scoring
    items_for_scoring = []
    for i, item in enumerate(memory_items):
        content = item.get('content', str(item))
        items_for_scoring.append({
            'id': i,
            'content': content[:200]  # Truncate for efficiency
        })
    
    scoring_prompt = f"""Score the relevance of each memory item for the current task.
Current query: "{current_query}"

Memory items to score:
{json.dumps(items_for_scoring, indent=2)}

Return JSON with relevance scores (0.0 to 1.0):
{{
  "0": 0.8,
  "1": 0.3,
  "2": 0.9
}}

Score based on:
- Semantic similarity to current query
- Contextual relevance to the task
- Potential usefulness for solving the problem"""
    
    try:
        response = llm_client.run([{"role": "user", "content": scoring_prompt}])
        
        # Extract scores
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            scores_dict = json.loads(response[start:end])
            
            # Apply scores and sort
            scored_items = []
            for i, item in enumerate(memory_items):
                score = float(scores_dict.get(str(i), 0.5))  # Default 0.5 if missing
                scored_items.append({
                    **item,
                    'relevance_score': score
                })
            
            # Sort by relevance (highest first) and return top items
            scored_items.sort(key=lambda x: x['relevance_score'], reverse=True)
            return scored_items[:max_items]
            
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback: return original order
        pass
    
    return memory_items[:max_items]


def relevant_context(
    cognition: Dict[str, Any],
    current_query: str,
    react_mode: str,
    llm_client
) -> List[Dict[str, Any]]:
    """Get relevant context based on react mode.
    
    Args:
        cognition: Current cognitive state
        current_query: Current user query
        react_mode: 'fast' or 'deep'
        llm_client: LLM client for scoring (deep mode only)
        
    Returns:
        List of relevant context items
    """
    action_history = cognition.get("action_history", [])
    failed_attempts = cognition.get("failed_attempts", [])
    
    if react_mode == "fast":
        # Fast mode: Simple FIFO, no LLM scoring
        max_history = 3
        return {
            'recent_actions': action_history[-max_history:],
            'recent_failures': failed_attempts[-2:] if failed_attempts else []
        }
    
    else:  # Deep mode
        # Deep mode: LLM-based relevance scoring
        max_history = 10
        
        # Combine action history and failures for scoring
        all_items = []
        
        # Add recent actions
        for i, action in enumerate(action_history[-15:]):  # Look at more items to score
            all_items.append({
                'type': 'action',
                'content': f"Action: {action}",
                'index': i
            })
        
        # Add failed attempts with more context
        for i, failure in enumerate(failed_attempts[-10:]):
            all_items.append({
                'type': 'failure', 
                'content': f"Failed attempt: {failure}",
                'index': i
            })
        
        if all_items:
            try:
                relevant_items = score_memory_relevance(
                    current_query, 
                    all_items, 
                    llm_client,
                    max_items=max_history
                )
                
                # Separate back into actions and failures
                relevant_actions = [
                    item for item in relevant_items 
                    if item.get('type') == 'action'
                ]
                relevant_failures = [
                    item for item in relevant_items 
                    if item.get('type') == 'failure'
                ]
                
                return {
                    'recent_actions': [item['content'].replace('Action: ', '') for item in relevant_actions],
                    'recent_failures': [item['content'].replace('Failed attempt: ', '') for item in relevant_failures]
                }
                
            except Exception:
                # Fallback to FIFO if LLM scoring fails
                pass
        
        # Fallback: FIFO with deep mode limits
        return {
            'recent_actions': action_history[-max_history:],
            'recent_failures': failed_attempts[-5:] if failed_attempts else []
        }