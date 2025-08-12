"""Document corpus search using canonical semantic interface."""

from resilient_result import Result

from cogency.semantic import search_json_index


async def search(
    query_embedding: list[float],
    file_path: str,
    top_k: int = 5,
    threshold: float = 0.0,
    filters: dict = None,
) -> Result:
    """Search pre-computed JSON embeddings using canonical semantic interface."""
    return await search_json_index(query_embedding, file_path, top_k, threshold, filters)
