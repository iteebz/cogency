"""LLM-based memory relevance scoring - pure semantic approach without heuristic approximations."""

import json
from typing import Any, Dict, List

DEFAULT_MAX_ITEMS_TO_SCORE = 5
DEFAULT_CONTENT_TRUNCATE_LENGTH = 200
DEFAULT_SCORE_FALLBACK = 0.5
FAST_MODE_MAX_HISTORY = 3
FAST_MODE_MAX_FAILURES_CONTEXT = 2
DEEP_MODE_MAX_HISTORY = 10
DEEP_MODE_MAX_DECISIONS_TO_SCORE = 5
DEEP_MODE_MAX_FAILURES_TO_SCORE = 3
DEEP_MODE_MAX_FAILURES_CONTEXT = 5


def score_memory_relevance(
    current_query: str,
    memory_items: List[Dict[str, Any]],
    llm_client,
    max_items: int = DEFAULT_MAX_ITEMS_TO_SCORE,
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
        content = item.get("content", str(item))
        items_for_scoring.append(
            {
                "id": i,
                "content": content[:DEFAULT_CONTENT_TRUNCATE_LENGTH],  # Truncate for efficiency
            }
        )

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

        # Use consolidated JSON parser
        from cogency.utils.parsing import parse_json_result

        parse_result = parse_json_result(response)
        if not parse_result.success:
            raise ValueError("Failed to parse LLM response for scoring")
        scores_dict = parse_result.data

        if scores_dict:
            # Apply scores and sort
            scored_items = []
            for i, item in enumerate(memory_items):
                score = float(
                    scores_dict.get(str(i), DEFAULT_SCORE_FALLBACK)
                )  # Default 0.5 if missing
                scored_items.append({**item, "relevance_score": score})

            # Sort by relevance (highest first) and return top items
            scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
            return scored_items[:max_items]

    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback: return original order
        pass

    return memory_items[:max_items]


def relevant_context(
    cognition: Dict[str, Any], current_query: str, react_mode: str, llm_client
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
    decision_history = cognition.get("decision_history", [])
    failed_attempts = cognition.get("failed_attempts", [])

    if react_mode == "fast":
        # Fast mode: Simple FIFO, no LLM scoring
        max_history = FAST_MODE_MAX_HISTORY
        return {
            "recent_decisions": decision_history[-max_history:],
            "recent_failures": failed_attempts[-FAST_MODE_MAX_FAILURES_CONTEXT:]
            if failed_attempts
            else [],
        }

    else:  # Deep mode
        # Deep mode: LLM-based relevance scoring
        max_history = DEEP_MODE_MAX_HISTORY

        # Combine action history and failures for scoring
        all_items = []

        # Add recent decisions
        for i, decision in enumerate(
            decision_history[-DEEP_MODE_MAX_DECISIONS_TO_SCORE:]
        ):  # Look at more items to score
            all_items.append({"type": "decision", "content": f"Decision: {decision}", "index": i})

        # Add failed attempts with more context
        for i, failure in enumerate(failed_attempts[-DEEP_MODE_MAX_FAILURES_TO_SCORE:]):
            all_items.append(
                {"type": "failure", "content": f"Failed attempt: {failure}", "index": i}
            )

        if all_items:
            try:
                relevant_items = score_memory_relevance(
                    current_query, all_items, llm_client, max_items=max_history
                )

                # Separate back into decisions and failures
                relevant_decisions = [
                    item for item in relevant_items if item.get("type") == "decision"
                ]
                relevant_failures = [
                    item for item in relevant_items if item.get("type") == "failure"
                ]

                return {
                    "recent_decisions": [
                        item["content"].replace("Decision: ", "") for item in relevant_decisions
                    ],
                    "recent_failures": [
                        item["content"].replace("Failed attempt: ", "")
                        for item in relevant_failures
                    ],
                }

            except Exception:
                # Fallback to FIFO if LLM scoring fails
                pass

        # Fallback: FIFO with deep mode limits
        return {
            "recent_decisions": decision_history[-max_history:],
            "recent_failures": failed_attempts[-DEEP_MODE_MAX_FAILURES_CONTEXT:]
            if failed_attempts
            else [],
        }
