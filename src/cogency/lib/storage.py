"""Storage: File system operations for persistence."""

import json
import time
from pathlib import Path
from typing import Any


def get_cogency_dir() -> Path:
    """Get ~/.cogency directory, create if needed."""
    cogency_dir = Path.home() / ".cogency"
    cogency_dir.mkdir(exist_ok=True)
    return cogency_dir


def load_json_file(path: Path, default: Any = None) -> Any:
    """Load JSON file with graceful degradation."""
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception:
        return default if default is not None else {}


def save_json_file(path: Path, data: Any) -> bool:
    """Save JSON file with error handling."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def load_conversations(user_id: str) -> list[dict]:
    """Load conversation history for user."""
    conv_file = get_cogency_dir() / "conversations" / f"{user_id}.json"
    result = load_json_file(conv_file, None)
    return result if result is not None else []


def save_conversations(user_id: str, messages: list[dict]) -> bool:
    """Save conversation history for user."""
    conv_file = get_cogency_dir() / "conversations" / f"{user_id}.json"
    return save_json_file(conv_file, messages)


def load_profile(user_id: str) -> dict:
    """Load user profile."""
    profile_file = get_cogency_dir() / "profiles" / f"{user_id}.json"
    return load_json_file(profile_file, {})


def save_profile(user_id: str, profile: dict) -> bool:
    """Save user profile."""
    profile_file = get_cogency_dir() / "profiles" / f"{user_id}.json"
    return save_json_file(profile_file, profile)


def load_knowledge() -> dict:
    """Load knowledge base."""
    knowledge_file = get_cogency_dir() / "knowledge" / "documents.json"
    return load_json_file(knowledge_file, {})


def save_knowledge(knowledge: dict) -> bool:
    """Save knowledge base."""
    knowledge_file = get_cogency_dir() / "knowledge" / "documents.json"
    return save_json_file(knowledge_file, knowledge)


def add_document(doc_id: str, content: str, metadata: dict = None) -> bool:
    """Add document to knowledge base."""
    try:
        knowledge = load_knowledge()
        knowledge[doc_id] = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        return save_knowledge(knowledge)
    except Exception:
        return False


async def search_documents(query: str, limit: int = 3, embedder=None) -> list[dict]:
    """Semantic search in knowledge base with keyword fallback."""
    try:
        knowledge = load_knowledge()
        if not knowledge:
            return []

        results = []

        if embedder:
            # Semantic search path - vector similarity
            try:
                query_result = await embedder.embed([query])
                if query_result.success:
                    query_embedding = query_result.unwrap()[0]
                    results = await _semantic_search(query_embedding, knowledge, limit)
                else:
                    # Fallback to keyword if embedding fails
                    results = _keyword_search(query, knowledge, limit)
            except Exception:
                # Graceful degradation to keyword search
                results = _keyword_search(query, knowledge, limit)
        else:
            # Keyword search fallback
            results = _keyword_search(query, knowledge, limit)

        return results
    except Exception:
        return []


def _keyword_search(query: str, knowledge: dict, limit: int) -> list[dict]:
    """Keyword-based search fallback."""
    results = []
    query_lower = query.lower()

    for doc_id, doc_data in knowledge.items():
        content = doc_data.get("content", "").lower()
        if query_lower in content:
            results.append(
                {
                    "doc_id": doc_id,
                    "content": doc_data.get("content", ""),
                    "metadata": doc_data.get("metadata", {}),
                    "relevance": content.count(query_lower),
                }
            )

    # Sort by relevance (simple word count)
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:limit]


async def _semantic_search(query_embedding: list[float], knowledge: dict, limit: int) -> list[dict]:
    """Vector similarity search with cosine similarity."""
    results = []

    for doc_id, doc_data in knowledge.items():
        doc_embedding = doc_data.get("embedding")
        if doc_embedding:
            similarity = _cosine_similarity(query_embedding, doc_embedding)
            results.append(
                {
                    "doc_id": doc_id,
                    "content": doc_data.get("content", ""),
                    "metadata": doc_data.get("metadata", {}),
                    "relevance": similarity,
                }
            )

    # Sort by semantic similarity
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:limit]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
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
