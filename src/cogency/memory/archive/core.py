"""Core archival memory logic - knowledge artifact extraction."""

from typing import Dict, List

from cogency.events import emit
from cogency.state import State


class ArchivalError(Exception):
    """Specific error for knowledge archival failures."""

    def __init__(self, message: str, stage: str):
        super().__init__(message)
        self.stage = stage


async def archive(state: State, memory) -> None:
    """Extract knowledge artifacts from completed conversation."""
    if not memory or not hasattr(memory, "archival") or not memory.archival:
        return

    emit("archive", state="start", user_id=state.user_id)

    try:
        # Extract insights from conversation history
        insights = await _extract_insights(state, memory)

        if not insights:
            emit("archive", state="skipped", reason="no_insights", user_id=state.user_id)
            return

        # Process each insight through consolidation pipeline
        consolidation_results = []
        for insight in insights:
            try:
                result = await _process_insight(insight, memory.archival, state.user_id)
                consolidation_results.append(result)
            except ArchivalError as e:
                emit(
                    "archive",
                    operation="insight_failed",
                    insight_topic=insight.get("topic"),
                    error=str(e),
                    stage=e.stage,
                    user_id=state.user_id,
                )
                continue

        successful_consolidations = len([r for r in consolidation_results if r])
        emit(
            "archive",
            state="complete",
            user_id=state.user_id,
            total_insights=len(insights),
            successful_consolidations=successful_consolidations,
        )

    except Exception as e:
        emit("archive", state="error", error=str(e), user_id=state.user_id)
        # Archival failures don't affect user experience


async def _extract_insights(state: State, memory) -> List[Dict]:
    """Extract knowledge insights from conversation history."""
    from resilient_result import unwrap

    from .prompt import build_extraction_prompt

    # Build extraction prompt from conversation
    prompt = build_extraction_prompt(state)

    # Get LLM extraction
    llm_result = await memory.provider.run([{"role": "user", "content": prompt}])
    response = unwrap(llm_result)

    # Parse JSON response
    import json

    try:
        data = json.loads(response)
        insights = data.get("insights", [])

        # Quality filter
        valid_insights = []
        for insight in insights:
            if _meets_quality_threshold(insight):
                valid_insights.append(insight)

        return valid_insights

    except json.JSONDecodeError:
        emit("archive", operation="extraction_parse_error", user_id=state.user_id)
        return []


async def _process_insight(insight: Dict, archival, user_id: str):
    """Process single insight through consolidation pipeline."""
    topic = insight["topic"]
    insight_content = insight["insight"]

    emit("archive", operation="insight_processing", user_id=user_id, topic=topic, stage="start")

    # Search for similar existing documents
    similar_docs = await archival.search_topics(
        user_id=user_id,
        query=topic,
        limit=3,
        min_similarity=0.8,  # Conservative threshold
    )

    if similar_docs:
        # Merge with highest similarity document
        target_doc = max(similar_docs, key=lambda doc: doc["similarity"])
        return await _merge_with_existing(insight, target_doc, archival, user_id)
    else:
        # Create new document
        return await archival.store_insight(user_id, topic, insight_content)


async def _merge_with_existing(insight: Dict, target_doc: Dict, archival, user_id: str):
    """Merge insight with existing document using specialized prompt."""
    from resilient_result import unwrap

    from .prompt import build_merge_prompt

    topic = insight["topic"]
    new_insight = insight["insight"]
    target_topic = target_doc["topic"]
    existing_content = target_doc["content"]

    # Build merge prompt
    prompt = build_merge_prompt(existing_content, new_insight)

    try:
        # Single LLM call for merge
        merge_result = await archival.llm.generate(prompt, "")
        merged_content = unwrap(merge_result)

        # Save merged document
        result = await archival._save_merged_topic(user_id, target_topic, merged_content)

        emit(
            "archive",
            operation="document_merge",
            user_id=user_id,
            source_topic=topic,
            target_topic=target_topic,
            stage="complete",
            merged_length=len(merged_content),
        )

        return result

    except Exception as e:
        # Fallback: create new document
        emit("archive", operation="merge_fallback", user_id=user_id, topic=topic, error=str(e))
        return await archival.store_insight(user_id, topic, new_insight)


def _meets_quality_threshold(insight: Dict) -> bool:
    """Quality validation for extracted insights."""
    insight_text = insight.get("insight", "")
    confidence = insight.get("confidence", 0)
    topic = insight.get("topic", "").strip()

    return (
        len(insight_text) > 20
        and confidence > 0.7
        and topic != ""
        and topic.lower() not in ["general", "misc", "other", "unknown"]
    )
