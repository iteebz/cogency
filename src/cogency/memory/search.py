"""Pure search logic for memory backends."""

import logging
from typing import Callable, List, Optional
from uuid import UUID

import numpy as np

from .core import Memory, SearchType

logger = logging.getLogger(__name__)


def cos_sim(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    try:
        a_np = np.array(a)
        b_np = np.array(b)

        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))
    except Exception as e:
        logger.error(f"Context: {e}")
        return 0.0


def text_score(content: str, query: str, tags: List[str]) -> float:
    """Calculate text-based relevance score."""
    if not query:
        return 0.0

    query_words = query.lower().split()
    content_lower = content.lower()
    score = 0.0

    # Exact phrase match
    if query.lower() in content_lower:
        score += 1.0  # TEXT_SCORE_EXACT_PHRASE_BOOST

    # Word frequency
    for word in query_words:
        score += content_lower.count(word) * 0.1  # TEXT_SCORE_WORD_FREQUENCY_BOOST

    # Tag matching
    for tag in tags:
        if any(word in tag.lower() for word in query_words):
            score += 0.5  # TEXT_SCORE_TAG_MATCHING_BOOST

    # Preference indicators boost relevance
    strong_preference_words = ["favorite", "best", "prefer"]
    mild_preference_words = ["love", "like", "enjoy"]

    for word in strong_preference_words:
        if word in content_lower:
            score += 0.7  # TEXT_SCORE_STRONG_PREFERENCE_BOOST
    for word in mild_preference_words:
        if word in content_lower:
            score += 0.3  # TEXT_SCORE_MILD_PREFERENCE_BOOST

    # Normalize by length - penalize longer content for same matches
    content_length = len(content.split())
    if content_length > 0:
        score = score / (1.0 + content_length * 0.02)  # TEXT_SCORE_NORMALIZATION_FACTOR

    return score


async def search(
    query: str,
    artifacts: List[Memory],
    search_type: SearchType,
    threshold: float,
    embedder=None,
    embed: Optional[Callable[[UUID], Optional[List[float]]]] = None,
) -> List[Memory]:
    """Execute search across artifacts."""
    if search_type == SearchType.TAGS:
        return artifacts  # Already filtered by caller

    query_embedding = None
    if search_type in [SearchType.SEMANTIC, SearchType.HYBRID] and embedder:
        embed_result = await embedder.embed_text(query)
        if embed_result.success:
            query_embedding = embed_result.data

    # Score artifacts
    for artifact in artifacts:
        score = 0.0

        if search_type in [SearchType.TEXT, SearchType.HYBRID, SearchType.AUTO]:
            score += text_score(artifact.content, query, artifact.tags)

        if search_type in [SearchType.SEMANTIC, SearchType.HYBRID] and query_embedding and embed:
            artifact_embedding = await embed(artifact.id)
            if artifact_embedding:
                semantic_score = cos_sim(query_embedding, artifact_embedding)
                score += semantic_score * 5.0  # Scale semantic score

        artifact.relevance_score = score

    # Filter and sort
    filtered = [a for a in artifacts if a.relevance_score >= threshold]
    return sorted(filtered, key=lambda x: x.relevance_score, reverse=True)
