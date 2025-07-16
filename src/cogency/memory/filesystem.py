"""Filesystem-based memory implementation for Cogency agents."""
import json
import os
import re
import asyncio
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from .base import BaseMemory, MemoryArtifact, MemoryType
from .filters import filter_artifacts
# from ..utils.profiling import CogencyProfiler  # Temporarily disabled for faster startup


class FSMemory(BaseMemory):
    """Filesystem-based memory backend.
    
    Stores memory artifacts as JSON files in a directory structure.
    Uses simple text matching for recall operations.
    """

    def __init__(self, memory_dir: str = ".memory"):
        """Initialize filesystem memory.
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        # self.profiler = CogencyProfiler()  # Temporarily disabled for faster startup
        self._executor = ThreadPoolExecutor(max_workers=4)  # For I/O operations
        self._cache = {}  # Simple in-memory cache
        self._pending_tasks = set()  # To keep track of cache expiration tasks
    
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
        timeout_seconds: float = 10.0
    ) -> MemoryArtifact:
        """Store content as JSON file."""
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Save as JSON file with UUID as filename
        file_path = self.memory_dir / f"{artifact.id}.json"
        artifact_data = {
            "id": str(artifact.id),
            "content": artifact.content,
            "memory_type": artifact.memory_type.value,
            "tags": artifact.tags,
            "metadata": artifact.metadata,
            "created_at": artifact.created_at.isoformat(),
            "confidence_score": artifact.confidence_score,
            "access_count": artifact.access_count,
            "last_accessed": artifact.last_accessed.isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, indent=2, ensure_ascii=False)
        
        return artifact

    async def recall(
        self, 
        query: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        since: Optional[str] = None,
        **kwargs
    ) -> List[MemoryArtifact]:
        """Search artifacts with enhanced relevance scoring and async optimization."""
        
        async def _recall_implementation():
            # Check cache first
            cache_key = f"{query}:{limit}:{tags}:{memory_type}:{since}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            artifacts = []
            query_lower = query.lower()
            query_words = query_lower.split()
            
            # Get all JSON files
            file_paths = list(self.memory_dir.glob("*.json"))
            
            # Process files in parallel batches
            batch_size = 10
            tasks = []
            
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i + batch_size]
                task = self._process_file_batch(batch, query_words, memory_type, tags, since)
                tasks.append(task)
            
            # Execute all batches concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results
            for batch_result in batch_results:
                if isinstance(batch_result, list):
                    artifacts.extend(batch_result)
            
            # Sort by combined score: relevance * decay_score
            artifacts.sort(key=lambda x: x.relevance_score * x.decay_score(), reverse=True)
            
            # Apply limit
            if limit:
                artifacts = artifacts[:limit]
            
            # Cache results for 60 seconds
            self._cache[cache_key] = artifacts
            task = asyncio.create_task(self._expire_cache_entry(cache_key, 60))
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)
            
            return artifacts
        
        # return await self.profiler.profile_memory_access(_recall_implementation)  # Temporarily disabled
        return await _recall_implementation()
    
    async def _process_file_batch(self, file_paths: List[Path], query_words: List[str], 
                                  memory_type: Optional[MemoryType], tags: Optional[List[str]], 
                                  since: Optional[str]) -> List[MemoryArtifact]:
        """Process a batch of files concurrently."""
        loop = asyncio.get_event_loop()
        
        def process_file(file_path: Path) -> Optional[MemoryArtifact]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Apply common filters
                if not filter_artifacts(data, memory_type, tags, since):
                    return None
                
                # Enhanced relevance scoring
                content_lower = data["content"].lower()
                relevance_score = self._calculate_relevance(content_lower, query_words, data["tags"])
                
                if relevance_score > 0:
                    artifact = MemoryArtifact(
                        content=data["content"],
                        memory_type=MemoryType(data.get("memory_type", MemoryType.FACT.value)),
                        id=UUID(data["id"]),
                        tags=data["tags"],
                        metadata=data["metadata"],
                        relevance_score=relevance_score,
                        confidence_score=data.get("confidence_score", 1.0),
                        access_count=data.get("access_count", 0),
                    )
                    # Parse datetimes
                    artifact.created_at = datetime.fromisoformat(data["created_at"])
                    artifact.last_accessed = datetime.fromisoformat(data.get("last_accessed", data["created_at"]))
                    
                    # Update access tracking asynchronously
                    artifact.access_count += 1
                    artifact.last_accessed = datetime.now(UTC)
                    
                    return artifact
                    
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted files
                return None
        
        # Process files concurrently using thread pool
        tasks = [loop.run_in_executor(self._executor, process_file, file_path) 
                for file_path in file_paths]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        artifacts = [r for r in results if isinstance(r, MemoryArtifact)]
        
        # Update access stats for all artifacts (fire and forget)
        for artifact in artifacts:
            asyncio.create_task(self._update_access_stats(artifact))
        
        return artifacts
    
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
    
    async def _update_access_stats(self, artifact: MemoryArtifact) -> None:
        """Update access statistics for an artifact."""
        file_path = self.memory_dir / f"{artifact.id}.json"
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

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove artifact file."""
        file_path = self.memory_dir / f"{artifact_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def clear(self) -> None:
        """Remove all artifact files."""
        for file_path in self.memory_dir.glob("*.json"):
            file_path.unlink()
    
    def _get_fs_stats(self) -> Dict[str, Any]:
        """Get filesystem-specific stats."""
        files = list(self.memory_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        return {
            "count": len(files),
            "total_size_kb": round(total_size / 1024, 1),
            "directory": str(self.memory_dir)
        }

    def close(self):
        """Shuts down the thread pool executor."""
        self._executor.shutdown(wait=True)