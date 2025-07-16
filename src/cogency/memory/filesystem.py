"""Filesystem-based memory implementation for Cogency agents."""
import json
import os
import re
import asyncio
import numpy as np
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from .base import BaseMemory, MemoryArtifact, MemoryType, SearchType
from .filters import filter_artifacts
# from ..utils.profiling import CogencyProfiler  # Temporarily disabled for faster startup


class FSMemory(BaseMemory):
    """Filesystem-based memory backend.
    
    Stores memory artifacts as JSON files in a directory structure.
    Uses simple text matching for recall operations.
    """

    def __init__(self, memory_dir: str = ".memory", embedding_provider=None):
        """Initialize filesystem memory.
        
        Args:
            memory_dir: Base directory to store memory files
            embedding_provider: Optional embedding provider for semantic search
        """
        super().__init__(embedding_provider)
        self.base_memory_dir = Path(memory_dir)
        self.base_memory_dir.mkdir(exist_ok=True)
        # self.profiler = CogencyProfiler()  # Temporarily disabled for faster startup
        self._executor = ThreadPoolExecutor(max_workers=4)  # For I/O operations
        self._cache = {}  # Simple in-memory cache
        self._pending_tasks = set()  # To keep track of cache expiration tasks
    
    def _get_user_memory_dir(self, user_id: str = "default") -> Path:
        """Get user-specific memory directory."""
        user_dir = self.base_memory_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def should_store(self, text: str) -> Tuple[bool, str]:
        """Smart auto-storage heuristics - NO BULLSHIT."""
        triggers = [
            (r"\bi am\b", "personal"),
            (r"\bi have\b", "personal"), 
            (r"\bi work\b", "work"),
            (r"\bi like\b", "preferences"),
            (r"\bmy name is\b", "personal"),
            (r"\badhd\b", "personal"),
            (r"\bsoftware engineer\b", "work"),
            (r"\bdeveloper\b", "work")
        ]
        
        text_lower = text.lower()
        for pattern, category in triggers:
            if re.search(pattern, text_lower):
                return True, category
        return False, ""

    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 10.0,
        user_id: str = "default"
    ) -> MemoryArtifact:
        """Store content as JSON file with optional embedding."""
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Generate embedding if provider available
        embedding = None
        if self.embedding_provider:
            try:
                embedding = await self.embedding_provider.embed(content)
            except Exception:
                # Fail gracefully if embedding fails
                pass
        
        # Save as JSON file with UUID as filename in user-specific directory
        memory_dir = self._get_user_memory_dir(user_id)
        file_path = memory_dir / f"{artifact.id}.json"
        artifact_data = {
            "id": str(artifact.id),
            "content": artifact.content,
            "memory_type": artifact.memory_type.value,
            "tags": artifact.tags,
            "metadata": artifact.metadata,
            "created_at": artifact.created_at.isoformat(),
            "confidence_score": artifact.confidence_score,
            "access_count": artifact.access_count,
            "last_accessed": artifact.last_accessed.isoformat(),
            "embedding": embedding  # Store embedding vector
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, indent=2, ensure_ascii=False)
        
        return artifact

    async def recall(
        self, 
        query: str,
        search_type: SearchType = SearchType.AUTO,
        limit: int = 10,
        threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        since: Optional[str] = None,
        user_id: str = "default",
        **kwargs
    ) -> List[MemoryArtifact]:
        """Search artifacts using unified search interface."""
        
        # Determine search method
        effective_search_type = self._determine_search_type(search_type)
        
        # Validate search type requirements
        if effective_search_type == SearchType.SEMANTIC and not self.embedding_provider:
            raise ValueError("Semantic search requested but no embedding provider available")
        
        async def _recall_implementation():
            # Check cache first
            cache_key = f"{user_id}:{query}:{effective_search_type.value}:{limit}:{threshold}:{tags}:{memory_type}:{metadata_filter}:{since}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Get all JSON files from user-specific directory
            memory_dir = self._get_user_memory_dir(user_id)
            file_paths = list(memory_dir.glob("*.json"))
            
            # Load and filter artifacts
            artifacts = []
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Apply filters
                    if not self._apply_filters(data, memory_type, tags, metadata_filter, since):
                        continue
                    
                    # Create artifact
                    artifact = self._create_artifact_from_data(data)
                    artifacts.append(artifact)
                    
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
            
            # Apply search method
            if effective_search_type == SearchType.SEMANTIC:
                artifacts = await self._semantic_search(query, artifacts, threshold)
            elif effective_search_type == SearchType.TEXT:
                artifacts = self._text_search(query, artifacts)
            elif effective_search_type == SearchType.HYBRID:
                artifacts = await self._hybrid_search(query, artifacts, threshold)
            
            # Sort by combined score: relevance * decay_score
            artifacts.sort(key=lambda x: x.relevance_score * x.decay_score(), reverse=True)
            
            # Apply limit
            artifacts = artifacts[:limit]
            
            # Update access stats for returned artifacts
            for artifact in artifacts:
                artifact.access_count += 1
                artifact.last_accessed = datetime.now(UTC)
                # Update stats in file asynchronously
                asyncio.create_task(self._update_access_stats(artifact, user_id))
            
            # Cache results for 60 seconds
            self._cache[cache_key] = artifacts
            task = asyncio.create_task(self._expire_cache_entry(cache_key, 60))
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)
            
            return artifacts
        
        return await _recall_implementation()
    
    
    async def _expire_cache_entry(self, cache_key: str, delay: float):
        """Remove cache entry after delay."""
        await asyncio.sleep(delay)
        self._cache.pop(cache_key, None)

    async def _cleanup_tasks(self):
        """Awaits all pending background tasks to ensure they complete."""
        if self._pending_tasks:
            await asyncio.gather(*self._pending_tasks, return_exceptions=True)
        self._pending_tasks.clear()
    
    def _calculate_relevance(self, content: str, query_words: List[str], tags: List[str]) -> float:
        """Calculate relevance score based on content and tag matching."""
        if not query_words:
            return 0.0
        
        score = 0.0
        
        # Exact phrase match gets highest score
        query_phrase = " ".join(query_words)
        if query_phrase in content:
            score += 2.0
        
        # Word frequency scoring
        for word in query_words:
            word_count = content.count(word)
            if word_count > 0:
                score += word_count * 0.5
        
        # Tag matching boost
        for tag in tags:
            if any(word in tag.lower() for word in query_words):
                score += 1.0
        
        # Normalize by content length to favor precise matches
        content_length = len(content.split())
        if content_length > 0:
            score = score / (content_length * 0.01)
        
        return min(score, 10.0)  # Cap at 10.0
    
    async def _update_access_stats(self, artifact: MemoryArtifact, user_id: str = "default") -> None:
        """Update access statistics for an artifact."""
        memory_dir = self._get_user_memory_dir(user_id)
        file_path = memory_dir / f"{artifact.id}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data["access_count"] = artifact.access_count
                data["last_accessed"] = artifact.last_accessed.isoformat()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            except (json.JSONDecodeError, KeyError, ValueError):
                pass  # Skip if corrupted

    async def forget(self, artifact_id: UUID, user_id: str = "default") -> bool:
        """Remove artifact file."""
        memory_dir = self._get_user_memory_dir(user_id)
        file_path = memory_dir / f"{artifact_id}.json"
        if file_path.exists():
            file_path.unlink()
            # Clear cache entries that might contain this artifact
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                self._cache.pop(key, None)
            return True
        return False

    async def clear(self, user_id: str = "default") -> None:
        """Remove all artifact files for a user."""
        memory_dir = self._get_user_memory_dir(user_id)
        for file_path in memory_dir.glob("*.json"):
            file_path.unlink()
        # Clear cache entries for this user
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            self._cache.pop(key, None)
    
    def _get_fs_stats(self, user_id: str = "default") -> Dict[str, Any]:
        """Get filesystem-specific stats for a user."""
        memory_dir = self._get_user_memory_dir(user_id)
        files = list(memory_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        return {
            "count": len(files),
            "total_size_kb": round(total_size / 1024, 1),
            "directory": str(memory_dir),
            "user_id": user_id
        }

    async def close(self):
        """Shuts down the thread pool executor and cleans up background tasks."""
        await self._cleanup_tasks()
        self._executor.shutdown(wait=True)
    
    def _determine_search_type(self, search_type: SearchType) -> SearchType:
        """Determine effective search type based on availability."""
        if search_type == SearchType.AUTO:
            # Choose semantic if embedding provider available, else text
            return SearchType.SEMANTIC if self.embedding_provider else SearchType.TEXT
        return search_type
    
    def _apply_filters(self, data: Dict[str, Any], memory_type: Optional[MemoryType], 
                      tags: Optional[List[str]], metadata_filter: Optional[Dict[str, Any]], 
                      since: Optional[str]) -> bool:
        """Apply standard filters to artifact data."""
        # Use existing filter logic
        return filter_artifacts(data, memory_type, tags, since) and self._metadata_filter_match(data, metadata_filter)
    
    def _metadata_filter_match(self, data: Dict[str, Any], metadata_filter: Optional[Dict[str, Any]]) -> bool:
        """Check if artifact metadata matches filter."""
        if not metadata_filter:
            return True
        
        artifact_metadata = data.get("metadata", {})
        for key, value in metadata_filter.items():
            if key not in artifact_metadata or artifact_metadata[key] != value:
                return False
        return True
    
    def _create_artifact_from_data(self, data: Dict[str, Any]) -> MemoryArtifact:
        """Create MemoryArtifact from JSON data."""
        artifact = MemoryArtifact(
            content=data["content"],
            memory_type=MemoryType(data.get("memory_type", MemoryType.FACT.value)),
            id=UUID(data["id"]),
            tags=data["tags"],
            metadata=data["metadata"],
            confidence_score=data.get("confidence_score", 1.0),
            access_count=data.get("access_count", 0),
        )
        # Parse datetimes
        artifact.created_at = datetime.fromisoformat(data["created_at"])
        artifact.last_accessed = datetime.fromisoformat(data.get("last_accessed", data["created_at"]))
        return artifact
    
    async def _semantic_search(self, query: str, artifacts: List[MemoryArtifact], threshold: float) -> List[MemoryArtifact]:
        """Perform semantic search using embeddings."""
        if not self.embedding_provider:
            return []
        
        # Generate query embedding
        query_embedding = await self.embedding_provider.embed(query)
        if not query_embedding:
            return []
        
        # Calculate similarities
        results = []
        for artifact in artifacts:
            # Get stored embedding
            memory_dir = self._get_user_memory_dir()
            file_path = memory_dir / f"{artifact.id}.json"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                stored_embedding = data.get("embedding")
                if stored_embedding:
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)
                    if similarity >= threshold:
                        artifact.relevance_score = similarity
                        results.append(artifact)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        return results
    
    def _text_search(self, query: str, artifacts: List[MemoryArtifact]) -> List[MemoryArtifact]:
        """Perform text-based search."""
        query_lower = query.lower()
        query_words = query_lower.split()
        
        results = []
        for artifact in artifacts:
            relevance_score = self._calculate_relevance(artifact.content.lower(), query_words, artifact.tags)
            if relevance_score > 0:
                artifact.relevance_score = relevance_score
                results.append(artifact)
        
        return results
    
    async def _hybrid_search(self, query: str, artifacts: List[MemoryArtifact], threshold: float) -> List[MemoryArtifact]:
        """Perform hybrid search combining semantic and text."""
        # Get both search results
        semantic_results = await self._semantic_search(query, artifacts, threshold * 0.5)  # Lower threshold for semantic
        text_results = self._text_search(query, artifacts)
        
        # Combine and deduplicate
        combined = {}
        
        # Add semantic results with higher weight
        for artifact in semantic_results:
            combined[artifact.id] = artifact
            artifact.relevance_score *= 1.2  # Boost semantic matches
        
        # Add text results
        for artifact in text_results:
            if artifact.id in combined:
                # Combine scores
                combined[artifact.id].relevance_score = (combined[artifact.id].relevance_score + artifact.relevance_score) / 2
            else:
                combined[artifact.id] = artifact
        
        return list(combined.values())
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            a_np = np.array(a)
            b_np = np.array(b)
            
            dot_product = np.dot(a_np, b_np)
            norm_a = np.linalg.norm(a_np)
            norm_b = np.linalg.norm(b_np)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        except Exception:
            return 0.0