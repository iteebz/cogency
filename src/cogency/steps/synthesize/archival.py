"""Archival memory consolidation - procedural pipeline for topic artifacts."""

from typing import Dict, List

from cogency.events import emit


class ConsolidationError(Exception):
    """Specific error for memory consolidation failures."""
    def __init__(self, message: str, stage: str):
        super().__init__(message)
        self.stage = stage


async def process_archival_insights(archival, user_id: str, insights: List[Dict]):
    """Process list of archival insights from synthesis using procedural pipeline."""
    if not insights:
        return
    
    emit("archival", operation="consolidation_start", user_id=user_id, insight_count=len(insights))
    
    consolidation_results = []
    
    for insight in insights:
        try:
            result = await _process_single_insight(insight, archival, user_id)
            consolidation_results.append(result)
            
        except ConsolidationError as e:
            # Specific, actionable error handling
            emit("archival", operation="consolidation_failed", 
                 insight_topic=insight.get("topic"),
                 error=str(e),
                 stage=e.stage,
                 user_id=user_id)
            continue
        except Exception as e:
            # Unexpected errors
            emit("archival", operation="consolidation_error",
                 insight_topic=insight.get("topic"), 
                 error=str(e),
                 user_id=user_id)
            continue
    
    successful_consolidations = len([r for r in consolidation_results if r])
    emit("archival", operation="consolidation_complete", 
         user_id=user_id,
         total_insights=len(insights),
         successful_consolidations=successful_consolidations)


async def _process_single_insight(insight: Dict, archival, user_id: str):
    """Clear procedural pipeline with explicit stages."""
    
    # Stage 1: Validate insight quality
    if not _meets_quality_threshold(insight):
        raise ConsolidationError(
            f"Insight below quality threshold: {insight}", 
            stage="validation"
        )
    
    topic = insight["topic"]
    insight_content = insight["insight"]
    
    emit("archival", operation="insight_processing", 
         user_id=user_id, topic=topic, stage="validated")
    
    # Stage 2: Semantic search with conservative threshold
    similar_docs = await archival.search_topics(
        user_id=user_id,
        query=topic, 
        limit=3,
        min_similarity=0.8  # Conservative threshold per AI Council guidance
    )
    
    emit("archival", operation="insight_processing",
         user_id=user_id, topic=topic, stage="searched",
         similar_docs_found=len(similar_docs))
    
    # Stage 3: Deterministic merge decision
    if similar_docs:
        # Always merge with highest similarity document (deterministic choice)
        target_doc = max(similar_docs, key=lambda doc: doc["similarity"])
        
        emit("archival", operation="insight_processing",
             user_id=user_id, topic=topic, stage="merging",
             target_topic=target_doc["topic"],
             similarity=target_doc["similarity"])
        
        return await _merge_with_target(insight, target_doc, archival, user_id)
    else:
        # Create new document
        emit("archival", operation="insight_processing",
             user_id=user_id, topic=topic, stage="creating_new")
        
        return await archival.store_insight(user_id, topic, insight_content)


def _meets_quality_threshold(insight: Dict) -> bool:
    """Explicit quality gates per AI Council guidance."""
    insight_text = insight.get("insight", "")
    confidence = insight.get("confidence", 0)
    topic = insight.get("topic", "").strip()
    
    return (
        len(insight_text) > 20 and
        confidence > 0.7 and
        topic != "" and
        topic.lower() not in ["general", "misc", "other", "unknown"]
    )


async def _merge_with_target(insight: Dict, target_doc: Dict, archival, user_id: str):
    """Merge new insight with highest similarity existing document."""
    from resilient_result import unwrap
    
    topic = insight["topic"]
    new_insight = insight["insight"]
    target_topic = target_doc["topic"]
    existing_content = target_doc["content"]
    
    emit("archival", operation="document_merge", 
         user_id=user_id, 
         source_topic=topic,
         target_topic=target_topic,
         stage="start")
    
    # Create specialized merge prompt
    merge_prompt = f"""Merge this new insight into the existing topic document.

EXISTING DOCUMENT:
{existing_content}

NEW INSIGHT: 
{new_insight}

MERGE INSTRUCTIONS:
- Integrate the new insight naturally into existing content
- Avoid duplication - if insight already exists, don't repeat it
- If contradictory, note both perspectives with context
- Maintain markdown structure and clear sections
- Update any "Last Updated" metadata
- Keep the tone consistent and concise

Return the complete updated document:"""
    
    try:
        # Single LLM call for specialized merge
        merge_result = await archival.llm.generate(merge_prompt, "")
        merged_content = unwrap(merge_result)
        
        # Save the merged document (update existing)
        result = await archival._save_merged_topic(user_id, target_topic, merged_content)
        
        emit("archival", operation="document_merge",
             user_id=user_id,
             source_topic=topic, 
             target_topic=target_topic,
             stage="complete",
             merged_length=len(merged_content))
        
        return result
        
    except Exception as e:
        emit("archival", operation="document_merge",
             user_id=user_id,
             source_topic=topic,
             target_topic=target_topic, 
             stage="error",
             error=str(e))
        
        # Fallback: create new document instead of merging
        return await archival.store_insight(user_id, topic, new_insight)