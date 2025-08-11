"""Archive search - pure semantic search functions."""

import math
from typing import Any

from resilient_result import unwrap

from cogency.events import emit


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


async def search_topics(
    embed_provider,
    user_id: str,
    query: str,
    embedding_cache: dict,
    limit: int = 3,
    min_similarity: float = 0.7,
) -> list[dict[str, Any]]:
    """Search topics using semantic similarity."""
    emit("memory", operation="search", user_id=user_id, query=query, status="start")

    try:
        # Generate query embedding
        embed_result = await embed_provider.embed(query)
        query_embedding = unwrap(embed_result)

        if isinstance(query_embedding, list) and query_embedding:
            query_vector = (
                query_embedding[0] if isinstance(query_embedding[0], list) else query_embedding
            )

            # Search cached embeddings
            results = []
            for cache_key, cached_data in embedding_cache.items():
                if not cache_key.startswith(f"{user_id}:"):
                    continue

                # Calculate cosine similarity
                similarity = cosine_similarity(query_vector, cached_data["embedding"])

                if similarity >= min_similarity:
                    results.append(
                        {
                            "topic": cached_data["topic"],
                            "content": cached_data["content"],
                            "similarity": similarity,
                            "updated": cached_data["updated"],
                        }
                    )

            # Sort by similarity and limit results
            results.sort(key=lambda x: x["similarity"], reverse=True)
            results = results[:limit]

            emit(
                "memory",
                operation="search",
                user_id=user_id,
                query=query,
                status="complete",
                results=len(results),
            )

            return results

        return []

    except Exception as e:
        emit(
            "memory",
            operation="search",
            user_id=user_id,
            query=query,
            status="error",
            error=str(e),
        )
        return []


async def update_embeddings(embed_provider, user_id: str, artifact, embedding_cache: dict) -> None:
    """Update vector embeddings for semantic search."""
    try:
        # Generate embedding for topic content
        embed_result = await embed_provider.embed(artifact.content)
        embedding = unwrap(embed_result)

        if isinstance(embedding, list) and embedding:
            # Store embedding
            cache_key = f"{user_id}:{artifact.topic}"
            embedding_cache[cache_key] = {
                "embedding": embedding[0] if isinstance(embedding[0], list) else embedding,
                "content": artifact.content,
                "topic": artifact.topic,
                "updated": artifact.updated,
            }

    except Exception as e:
        emit(
            "memory",
            operation="embed",
            user_id=user_id,
            topic=artifact.topic,
            status="error",
            error=str(e),
        )
        # Non-critical error - continue without embeddings
