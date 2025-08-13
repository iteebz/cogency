"""Sophisticated knowledge extraction and synthesis."""

import json
from typing import Any

from cogency.events import emit
from cogency.knowledge.types import KnowledgeArtifact

from .prompts import build_extraction_prompt


async def extract(state, memory) -> None:
    """Extract knowledge artifacts from completed conversation using sophisticated LLM synthesis."""
    if not memory or not state.execution or not state.execution.response:
        return

    emit("knowledge", state="extraction_start", user_id=state.user_id)

    try:
        # Extract knowledge using LLM synthesis
        knowledge_items = await _extract_knowledge_artifacts(
            query=state.query,
            response=state.execution.response,
            user_id=state.user_id,
            llm=memory.provider,
        )

        if not knowledge_items:
            emit(
                "knowledge",
                state="extraction_skipped",
                reason="no_knowledge",
                user_id=state.user_id,
            )
            return

        # Store knowledge artifacts using SOPHISTICATED CONSOLIDATION logic
        from cogency.storage import SQLite

        store = SQLite()

        stored_count = 0
        merged_count = 0

        for artifact in knowledge_items:
            try:
                # CONSOLIDATION: Search for similar existing knowledge
                similar_artifacts = await store.search_knowledge(
                    query=artifact.topic,
                    user_id=artifact.user_id,
                    top_k=3,
                    threshold=0.8,  # Conservative threshold for similarity
                )

                # Additional similarity check using content overlap
                if similar_artifacts:
                    most_similar = similar_artifacts[0]
                    if not _should_merge_artifacts(artifact, most_similar):
                        similar_artifacts = []  # Skip merge if not truly similar enough

                if similar_artifacts:
                    # MERGE: Use LLM to merge with most similar existing knowledge
                    most_similar = similar_artifacts[0]
                    merged_artifact = await _merge_with_existing_knowledge(
                        new_artifact=artifact, existing_artifact=most_similar, llm=memory.provider
                    )

                    if merged_artifact:
                        # Delete old and save merged
                        await store.delete_knowledge(most_similar.topic, most_similar.user_id)
                        success = await store.save_knowledge(merged_artifact)
                        if success:
                            merged_count += 1
                            emit(
                                "knowledge",
                                state="merged",
                                old_topic=most_similar.topic,
                                new_topic=artifact.topic,
                            )
                    else:
                        # Merge failed, store as new
                        success = await store.save_knowledge(artifact)
                        if success:
                            stored_count += 1
                else:
                    # No similar knowledge found, store as new
                    success = await store.save_knowledge(artifact)
                    if success:
                        stored_count += 1

            except Exception as e:
                emit("knowledge", state="consolidation_error", topic=artifact.topic, error=str(e))
                # Fallback: try to store without consolidation
                try:
                    success = await store.save_knowledge(artifact)
                    if success:
                        stored_count += 1
                except Exception:
                    continue

        emit(
            "knowledge",
            state="extraction_complete",
            user_id=state.user_id,
            extracted=len(knowledge_items),
            stored=stored_count,
            merged=merged_count,
        )

    except Exception as e:
        emit("knowledge", state="extraction_error", error=str(e), user_id=state.user_id)
        # Knowledge extraction failures don't affect user experience


async def _extract_knowledge_artifacts(
    query: str, response: str, user_id: str, llm
) -> list[KnowledgeArtifact]:
    """Extract knowledge artifacts using sophisticated LLM prompts."""

    # Build extraction prompt
    prompt = build_extraction_prompt(query, response, user_id)

    # Get LLM extraction
    result = await llm.generate([{"role": "user", "content": prompt}])
    if not result.success:
        emit("knowledge", state="llm_error", error="LLM call failed")
        return []

    # Parse JSON response
    try:
        data = json.loads(result.unwrap())
        knowledge_items = data.get("knowledge", [])
    except (json.JSONDecodeError, AttributeError):
        emit("knowledge", state="parse_error", error="JSON parse failed")
        return []

    # Quality filter and convert to artifacts
    artifacts = []
    for item in knowledge_items:
        if _meets_quality_threshold(item):
            artifact = KnowledgeArtifact(
                topic=item["topic"],
                content=item["knowledge"],
                confidence=item.get("confidence", 0.8),
                context=item.get("context", ""),
                user_id=user_id,
            )
            artifacts.append(artifact)

    return artifacts


def _meets_quality_threshold(knowledge_item: dict[str, Any]) -> bool:
    """Quality validation for extracted knowledge."""
    content = knowledge_item.get("knowledge", "")
    confidence = knowledge_item.get("confidence", 0)
    topic = knowledge_item.get("topic", "").strip()

    return (
        len(content) > 20
        and confidence >= 0.7
        and topic != ""
        and topic.lower() not in ["general", "misc", "other", "unknown"]
    )


async def _merge_with_existing_knowledge(
    new_artifact: KnowledgeArtifact, existing_artifact: KnowledgeArtifact, llm
) -> KnowledgeArtifact | None:
    """Merge new knowledge with existing artifact using sophisticated LLM prompts."""
    from datetime import datetime

    from .prompts import build_merge_prompt

    try:
        # Build merge prompt using existing sophisticated prompts
        merge_prompt = build_merge_prompt(
            existing_content=existing_artifact.content, new_knowledge=new_artifact.content
        )

        # Use LLM to perform intelligent merge
        result = await llm.generate([{"role": "user", "content": merge_prompt}])
        if not result.success:
            emit("knowledge", state="merge_llm_error", error="LLM merge call failed")
            return None

        merged_content = result.unwrap().strip()

        # Validate merge quality before creating artifact
        if not _validate_merge_quality(
            existing_artifact.content, new_artifact.content, merged_content
        ):
            emit(
                "knowledge",
                state="merge_quality_failed",
                existing_topic=existing_artifact.topic,
                new_topic=new_artifact.topic,
                reason="quality validation failed",
            )
            return None

        # Create merged artifact with updated metadata
        merged_artifact = KnowledgeArtifact(
            topic=existing_artifact.topic,  # Keep existing topic
            content=merged_content,
            confidence=max(new_artifact.confidence, existing_artifact.confidence),
            context=f"{existing_artifact.context}; {new_artifact.context}".strip("; "),
            user_id=existing_artifact.user_id,
            created_at=existing_artifact.created_at,  # Preserve original creation
            updated_at=datetime.now(),  # Update timestamp
            source_conversations=list(
                set(existing_artifact.source_conversations + new_artifact.source_conversations)
            ),
            metadata={**existing_artifact.metadata, **new_artifact.metadata},
        )

        emit(
            "knowledge",
            state="merge_success",
            existing_topic=existing_artifact.topic,
            new_topic=new_artifact.topic,
            merged_length=len(merged_content),
        )

        return merged_artifact

    except Exception as e:
        emit("knowledge", state="merge_error", error=str(e))
        return None


def _validate_merge_quality(existing_content: str, new_content: str, merged_content: str) -> bool:
    """Validate that merge actually improves knowledge quality."""
    # Basic sanity checks
    if not merged_content or len(merged_content) < 20:
        return False

    # Merged content should be substantial compared to individual pieces
    min_expected_length = min(len(existing_content), len(new_content))
    if len(merged_content) < min_expected_length * 0.8:
        return False  # Merge lost too much information

    # Check for reasonable maximum length (avoid runaway merging)
    max_reasonable_length = max(len(existing_content), len(new_content)) * 2
    if len(merged_content) > max_reasonable_length:
        return False  # Merge created excessive content

    # Ensure merged content isn't just concatenation without synthesis
    combined_length = len(existing_content) + len(new_content)
    if len(merged_content) > combined_length * 0.9:
        # Check if it's just concatenation by looking for both pieces
        existing_words = set(existing_content.lower().split())
        new_words = set(new_content.lower().split())
        merged_words = set(merged_content.lower().split())

        # If merged content contains almost all words from both, likely concatenation
        combined_unique_words = existing_words | new_words
        if len(merged_words & combined_unique_words) > len(combined_unique_words) * 0.95:
            return False  # Likely just concatenation, not synthesis

    # Check for duplicate sentences (poor merge quality indicator)
    sentences = [s.strip() for s in merged_content.split(".") if s.strip()]
    return len(sentences) == len(set(sentences))


def _should_merge_artifacts(
    new_artifact: KnowledgeArtifact, existing_artifact: KnowledgeArtifact
) -> bool:
    """Determine if two artifacts are similar enough to warrant merging."""
    # Check topic similarity beyond just vector similarity
    new_topic_words = set(new_artifact.topic.lower().split())
    existing_topic_words = set(existing_artifact.topic.lower().split())

    # Require at least some topic word overlap
    if not (new_topic_words & existing_topic_words):
        return False

    # Check content overlap to avoid merging unrelated content
    new_words = set(new_artifact.content.lower().split())
    existing_words = set(existing_artifact.content.lower().split())

    # Calculate Jaccard similarity for content
    intersection = new_words & existing_words
    union = new_words | existing_words

    if len(union) == 0:
        return False

    jaccard_similarity = len(intersection) / len(union)

    # Only merge if there's meaningful content overlap (>20%) and confidence is reasonable
    return (
        jaccard_similarity > 0.2
        and new_artifact.confidence > 0.7
        and existing_artifact.confidence > 0.7
    )
