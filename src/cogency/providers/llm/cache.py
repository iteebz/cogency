"""LLM response caching for performance optimization."""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    response: str
    timestamp: float
    hit_count: int = 0
    tokens_saved: int = 0


class LLMCache:
    """Smart LLM response cache with TTL and size limits."""

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,  # 1 hour default
        enable_stats: bool = True,
    ):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._enable_stats = enable_stats
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "total_tokens_saved": 0}
        self._lock = asyncio.Lock()

    def _generate_key(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate cache key from messages and parameters."""
        # Create deterministic hash from messages and kwargs
        content = str(messages) + str(sorted(kwargs.items()))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry has expired."""
        return time.time() - entry.timestamp > self._ttl_seconds

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average)."""
        return len(text) // 4

    async def get(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Get cached response if available and valid."""
        async with self._lock:
            cache_key = self._generate_key(messages, **kwargs)

            if cache_key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[cache_key]

            # Check expiration
            if self._is_expired(entry):
                del self._cache[cache_key]
                self._stats["misses"] += 1
                return None

            # Update hit statistics
            entry.hit_count += 1
            entry.tokens_saved += self._estimate_tokens(entry.response)
            self._stats["hits"] += 1
            self._stats["total_tokens_saved"] += self._estimate_tokens(entry.response)

            logger.debug(
                f"Cache hit for key {cache_key[:8]}... (saved ~{self._estimate_tokens(entry.response)} tokens)"
            )
            return entry.response

    async def set(self, messages: List[Dict[str, str]], response: str, **kwargs) -> None:
        """Cache LLM response with metadata."""
        async with self._lock:
            cache_key = self._generate_key(messages, **kwargs)

            # Enforce size limit with LRU eviction
            if len(self._cache) >= self._max_size:
                await self._evict_oldest()

            entry = CacheEntry(response=response, timestamp=time.time(), tokens_saved=0)

            self._cache[cache_key] = entry
            logger.debug(
                f"Cached response for key {cache_key[:8]}... ({self._estimate_tokens(response)} tokens)"
            )

    async def _evict_oldest(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return

        # Sort by timestamp and remove oldest 10%
        sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].timestamp)

        evict_count = max(1, len(sorted_entries) // 10)
        for key, _ in sorted_entries[:evict_count]:
            del self._cache[key]
            self._stats["evictions"] += 1

    async def clear(self) -> None:
        """Clear all cached entries."""
        async with self._lock:
            self._cache.clear()
            logger.info("LLM cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self._stats,
            "cache_size": len(self._cache),
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._max_size > 0
