"""CANONICAL semantic search - minimal, no bullshit."""

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from resilient_result import Result


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Pure cosine similarity - no bullshit."""
    if len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def rank_by_similarity(results: list[dict], top_k: int = 5, threshold: float = 0.0) -> list[dict]:
    """Pure ranking function - no bullshit."""
    # Filter by threshold
    filtered = [r for r in results if r.get('similarity', 0) >= threshold]
    
    # Sort by similarity descending
    filtered.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    
    # Take top-k
    return filtered[:top_k]


async def search_json_index(query_embedding: list[float], file_path: str, 
                          top_k: int = 5, threshold: float = 0.0, 
                          filters: dict = None) -> Result:
    """Search pre-computed JSON embeddings - RETRIEVAL pattern."""
    try:
        path = Path(file_path)
        if not path.exists():
            return Result.fail(f"Embeddings file not found: {file_path}")
        
        with open(path) as f:
            data = json.load(f)
        
        embeddings = data.get("embeddings", [])
        documents = data.get("documents", [])
        
        if len(embeddings) != len(documents):
            return Result.fail("Embeddings and documents length mismatch")
        
        if not embeddings:
            return Result.ok([])
        
        # Convert to numpy for vectorized computation
        embeddings_array = np.array(embeddings, dtype=np.float32)
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        # Vectorized cosine similarity
        embeddings_norm = embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        query_norm = query_vec / np.linalg.norm(query_vec)
        similarities = np.dot(embeddings_norm, query_norm)
        
        # Build results
        results = []
        for i, (doc, similarity) in enumerate(zip(documents, similarities)):
            # Apply metadata filters if provided
            if filters:
                doc_metadata = doc.get("metadata", {})
                if not all(doc_metadata.get(k) == v for k, v in filters.items()):
                    continue
            
            results.append({
                "content": doc["content"],
                "metadata": doc.get("metadata", {}),
                "similarity": float(similarity)
            })
        
        # Rank and filter
        ranked = rank_by_similarity(results, top_k, threshold)
        return Result.ok(ranked)
        
    except Exception as e:
        return Result.fail(f"JSON search failed: {str(e)}")


async def search_sqlite_vectors(query_embedding: list[float], db_connection, user_id: str,
                               top_k: int = 5, threshold: float = 0.0) -> Result:
    """Search SQLite vector table - RECALL pattern."""
    try:
        cursor = db_connection.cursor()
        
        # Get all vectors for user
        cursor.execute("""
            SELECT content, metadata, embedding 
            FROM knowledge_vectors 
            WHERE user_id = ?
        """, (user_id,))
        
        rows = cursor.fetchall()
        if not rows:
            return Result.ok([])
        
        # Compute similarities
        results = []
        for content, metadata_json, embedding_json in rows:
            stored_embedding = json.loads(embedding_json)
            similarity = cosine_similarity(query_embedding, stored_embedding)
            
            results.append({
                "content": content,
                "metadata": json.loads(metadata_json) if metadata_json else {},
                "similarity": similarity
            })
        
        # Rank and filter
        ranked = rank_by_similarity(results, top_k, threshold)
        return Result.ok(ranked)
        
    except Exception as e:
        return Result.fail(f"SQLite search failed: {str(e)}")


async def add_sqlite_vector(db_connection, user_id: str, content: str, 
                          metadata: dict, embedding: list[float]) -> Result:
    """Add vector to SQLite - RECALL pattern."""
    try:
        cursor = db_connection.cursor()
        
        cursor.execute("""
            INSERT INTO knowledge_vectors (user_id, content, metadata, embedding)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            content,
            json.dumps(metadata),
            json.dumps(embedding)
        ))
        
        db_connection.commit()
        return Result.ok(True)
        
    except Exception as e:
        return Result.fail(f"Vector storage failed: {str(e)}")


async def semantic_search(embedder, query: str, **search_kwargs) -> Result:
    """Universal semantic search function."""
    try:
        # Generate query embedding
        embed_result = await embedder.embed([query])
        if embed_result.failure:
            return Result.fail(f"Query embedding failed: {embed_result.error}")
        
        query_embedding = embed_result.data[0]
        
        # Delegate to appropriate search function based on kwargs
        if 'file_path' in search_kwargs:
            # JSON file search (Retrieval)
            return await search_json_index(query_embedding, **search_kwargs)
        elif 'db_connection' in search_kwargs:
            # SQLite search (Recall)
            return await search_sqlite_vectors(query_embedding, **search_kwargs)
        else:
            return Result.fail("Must provide either file_path or db_connection")
        
    except Exception as e:
        return Result.fail(f"Semantic search failed: {str(e)}")