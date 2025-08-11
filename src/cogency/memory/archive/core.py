"""Core archival memory logic - knowledge artifact extraction."""

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
        # Extract knowledge from conversation history
        knowledge_items = await _extract_knowledge(state, memory)

        if not knowledge_items:
            emit("archive", state="skipped", reason="no_knowledge", user_id=state.user_id)
            return

        # Process each knowledge item through consolidation pipeline
        consolidation_results = []
        for knowledge in knowledge_items:
            try:
                result = await _process_knowledge(knowledge, memory.archival, state.user_id)
                consolidation_results.append(result)
            except ArchivalError as e:
                emit(
                    "archive",
                    operation="knowledge_failed",
                    knowledge_topic=knowledge.get("topic"),
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
            total_knowledge_items=len(knowledge_items),
            successful_consolidations=successful_consolidations,
        )

    except Exception as e:
        emit("archive", state="error", error=str(e), user_id=state.user_id)
        # Archival failures don't affect user experience


async def _extract_knowledge(state: State, memory) -> list[dict]:
    """Extract knowledge from conversation history."""
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
        knowledge_items = data.get("knowledge", [])

        # Quality filter
        valid_knowledge = []
        for knowledge in knowledge_items:
            if _meets_quality_threshold(knowledge):
                valid_knowledge.append(knowledge)

        return valid_knowledge

    except json.JSONDecodeError:
        emit("archive", operation="extraction_parse_error", user_id=state.user_id)
        return []


async def _process_knowledge(knowledge: dict, archival, user_id: str):
    """Process single knowledge item through consolidation pipeline."""
    topic = knowledge["topic"]
    knowledge_content = knowledge["knowledge"]

    emit("archive", operation="knowledge_processing", user_id=user_id, topic=topic, stage="start")

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
        return await _merge_with_existing(knowledge, target_doc, archival, user_id)
    # Create new document
    return await archival.store_knowledge(user_id, topic, knowledge_content)


async def _merge_with_existing(knowledge: dict, target_doc: dict, archival, user_id: str):
    """Merge knowledge with existing document using specialized prompt."""
    from resilient_result import unwrap

    from .prompt import build_merge_prompt

    topic = knowledge["topic"]
    new_knowledge = knowledge["knowledge"]
    target_topic = target_doc["topic"]
    existing_content = target_doc["content"]

    # Build merge prompt
    prompt = build_merge_prompt(existing_content, new_knowledge)

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
        return await archival.store_knowledge(user_id, topic, new_knowledge)


def _meets_quality_threshold(knowledge: dict) -> bool:
    """Quality validation for extracted knowledge."""
    knowledge_text = knowledge.get("knowledge", "")
    confidence = knowledge.get("confidence", 0)
    topic = knowledge.get("topic", "").strip()

    return (
        len(knowledge_text) > 20
        and confidence > 0.7
        and topic != ""
        and topic.lower() not in ["general", "misc", "other", "unknown"]
    )
