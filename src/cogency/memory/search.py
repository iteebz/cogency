"""Pure search logic for memory backends."""
import numpy as np
from typing import List, Optional, Callable
from uuid import UUID

from .core import MemoryArtifact, SearchType


def cosine_similarity(a: List[float], b: List[float]) -> float:
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
    except Exception:
        return 0.0


def text_relevance(content: str, query: str, tags: List[str]) -> float:
    """Calculate text-based relevance score."""
    if not query:
        return 0.0
    
    query_words = query.lower().split()
    content_lower = content.lower()
    score = 0.0
    
    # Exact phrase match
    if query.lower() in content_lower:
        score += 2.0
    
    # Word frequency
    for word in query_words:
        score += content_lower.count(word) * 0.5
    
    # Tag matching
    for tag in tags:
        if any(word in tag.lower() for word in query_words):
            score += 1.0
    
    # Preference indicators boost relevance 
    strong_preference_words = ["favorite", "best", "prefer"]
    mild_preference_words = ["love", "like", "enjoy"]
    
    for word in strong_preference_words:
        if word in content_lower:
            score += 1.0
    for word in mild_preference_words:
        if word in content_lower:
            score += 0.5
    
    # Normalize by length - penalize longer content for same matches
    content_length = len(content.split())
    if content_length > 0:
        score = score / (1.0 + content_length * 0.02)
    
    return score


async def search_artifacts(
    query: str,
    artifacts: List[MemoryArtifact],
    search_type: SearchType,
    threshold: float,
    embedding_provider=None,
    get_embedding: Optional[Callable[[UUID], Optional[List[float]]]] = None
) -> List[MemoryArtifact]:
    """Execute search across artifacts."""
    if search_type == SearchType.TAGS:
        return artifacts  # Already filtered by caller
    
    query_embedding = None
    if search_type in [SearchType.SEMANTIC, SearchType.HYBRID] and embedding_provider:
        try:
            query_embedding = await embedding_provider.embed_text(query)
        except Exception:
            pass
    
    # Score artifacts
    for artifact in artifacts:
        score = 0.0
        
        if search_type in [SearchType.TEXT, SearchType.HYBRID, SearchType.AUTO]:
            score += text_relevance(artifact.content, query, artifact.tags)
        
        if search_type in [SearchType.SEMANTIC, SearchType.HYBRID] and query_embedding and get_embedding:
            artifact_embedding = await get_embedding(artifact.id)
            if artifact_embedding:
                semantic_score = cosine_similarity(query_embedding, artifact_embedding)
                score += semantic_score * 5.0  # Scale semantic score
        
        artifact.relevance_score = score
    
    # Filter and sort
    filtered = [a for a in artifacts if a.relevance_score >= threshold]
    return sorted(filtered, key=lambda x: x.relevance_score, reverse=True)