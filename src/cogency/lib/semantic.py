"""Semantic utilities: Vector similarity operations."""


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    try:
        # Dot product
        dot_product = sum(x * y for x, y in zip(a, b))

        # Magnitudes
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
    except Exception:
        return 0.0


def similarity_search(
    query_embedding: list[float],
    documents: dict[str, dict],
    limit: int = 5,
    embedding_key: str = "embedding",
) -> list[tuple[str, float]]:
    """Find most similar documents by cosine similarity.

    Returns: [(doc_id, similarity_score), ...]
    """
    results = []

    for doc_id, doc_data in documents.items():
        doc_embedding = doc_data.get(embedding_key)
        if doc_embedding:
            similarity = cosine_similarity(query_embedding, doc_embedding)
            results.append((doc_id, similarity))

    # Sort by similarity descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]
