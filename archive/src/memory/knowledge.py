"""CANONICAL knowledge extraction and storage - replaces broken archive system."""

import json
from typing import Any

from resilient_result import Result, unwrap

from cogency.events import emit
from cogency.semantic import add_sqlite_vector
from cogency.storage.state import SQLite


async def extract_and_store_knowledge(
    user_id: str, conversation_messages: list[dict], llm, embedder
) -> Result[dict]:
    """Extract knowledge from conversation and store in SQLite vectors.
    
    This replaces the entire broken archive system with simple, working code.
    """
    if not conversation_messages:
        return Result.ok({"extracted": 0, "stored": 0})
    
    try:
        emit("knowledge", operation="extract", user_id=user_id, status="start")
        
        # Build extraction prompt from conversation
        conversation_text = _format_conversation_for_extraction(conversation_messages)
        
        extraction_prompt = f"""
        Extract key knowledge and insights from this conversation that would be valuable to remember for future conversations.

        Focus on:
        - Technical insights, tips, or solutions
        - Important facts or information discovered
        - Useful patterns or approaches
        - Domain-specific knowledge

        Return a JSON object with this format:
        {{
            "knowledge_items": [
                {{
                    "topic": "Brief topic name",
                    "content": "Detailed knowledge content",
                    "confidence": 0.9
                }}
            ]
        }}

        Only extract knowledge with high confidence (>0.8). Skip general conversation or low-value content.

        Conversation:
        {conversation_text}
        """
        
        # Extract knowledge using LLM
        llm_result = await llm.generate("You are a knowledge extraction specialist.", extraction_prompt)
        response_text = unwrap(llm_result)
        
        # Parse JSON response
        try:
            data = json.loads(response_text)
            knowledge_items = data.get("knowledge_items", [])
        except json.JSONDecodeError:
            emit("knowledge", operation="extract", user_id=user_id, status="parse_error")
            return Result.fail("Failed to parse knowledge extraction response")
        
        if not knowledge_items:
            emit("knowledge", operation="extract", user_id=user_id, status="no_knowledge")
            return Result.ok({"extracted": 0, "stored": 0})
        
        # Quality filter
        valid_knowledge = [
            k for k in knowledge_items 
            if _is_valid_knowledge(k)
        ]
        
        if not valid_knowledge:
            return Result.ok({"extracted": len(knowledge_items), "stored": 0})
        
        # Store knowledge in SQLite vectors
        store = SQLite()
        await store._ensure_schema()
        
        stored_count = 0
        
        import aiosqlite
        async with aiosqlite.connect(store.db_path) as db:
            for knowledge in valid_knowledge:
                # Generate embedding for the knowledge content
                embed_result = await embedder.embed([knowledge["content"]])
                if embed_result.failure:
                    continue
                
                embedding = embed_result.data[0]
                
                # Check for similar existing knowledge to avoid duplication
                similar_exists = await _check_similar_knowledge(
                    db, user_id, embedding, knowledge["topic"], threshold=0.85
                )
                
                if similar_exists:
                    emit(
                        "knowledge", 
                        operation="store", 
                        user_id=user_id, 
                        topic=knowledge["topic"],
                        status="duplicate_skipped"
                    )
                    continue
                
                # Store new knowledge
                metadata = {
                    "topic": knowledge["topic"],
                    "confidence": knowledge["confidence"],
                    "extracted_from": "conversation",
                }
                
                store_result = await add_sqlite_vector(
                    db, user_id, knowledge["content"], metadata, embedding
                )
                
                if store_result.success:
                    stored_count += 1
                    emit(
                        "knowledge",
                        operation="store",
                        user_id=user_id,
                        topic=knowledge["topic"],
                        status="stored"
                    )
        
        emit(
            "knowledge",
            operation="extract",
            user_id=user_id,
            status="complete",
            extracted=len(valid_knowledge),
            stored=stored_count
        )
        
        return Result.ok({
            "extracted": len(valid_knowledge),
            "stored": stored_count,
            "topics": [k["topic"] for k in valid_knowledge[:stored_count]]
        })
        
    except Exception as e:
        emit("knowledge", operation="extract", user_id=user_id, status="error", error=str(e))
        return Result.fail(f"Knowledge extraction failed: {str(e)}")


def _format_conversation_for_extraction(messages: list[dict]) -> str:
    """Format conversation messages for knowledge extraction."""
    formatted_messages = []
    
    for msg in messages[-10:]:  # Last 10 messages to avoid token limits
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if role == "user":
            formatted_messages.append(f"User: {content}")
        elif role == "assistant":
            formatted_messages.append(f"Assistant: {content}")
    
    return "\n\n".join(formatted_messages)


def _is_valid_knowledge(knowledge: dict) -> bool:
    """Quality validation for extracted knowledge."""
    topic = knowledge.get("topic", "").strip()
    content = knowledge.get("content", "").strip()
    confidence = knowledge.get("confidence", 0)
    
    return (
        len(content) > 30  # Substantial content
        and confidence > 0.8  # High confidence
        and len(topic) > 3  # Meaningful topic
        and topic.lower() not in ["general", "misc", "other", "unknown", "conversation"]
        and not topic.lower().startswith("the ")  # Avoid generic topics
    )


async def _check_similar_knowledge(
    db_connection, user_id: str, query_embedding: list[float], 
    topic: str, threshold: float = 0.85
) -> bool:
    """Check if similar knowledge already exists to avoid duplication."""
    try:
        from cogency.semantic import cosine_similarity
        
        cursor = db_connection.cursor()
        
        # Get existing knowledge for this user
        cursor.execute("""
            SELECT content, metadata, embedding 
            FROM knowledge_vectors 
            WHERE user_id = ?
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        for content, metadata_json, embedding_json in rows:
            stored_embedding = json.loads(embedding_json)
            similarity = cosine_similarity(query_embedding, stored_embedding)
            
            if similarity >= threshold:
                return True
        
        return False
        
    except Exception:
        # If similarity check fails, allow storage to be safe
        return False