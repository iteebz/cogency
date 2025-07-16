"""ChromaDB vector database memory backend."""
import json
import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

from .base import BaseMemory, MemoryArtifact, MemoryType, SearchType


class ChromaDBMemory(BaseMemory):
    """ChromaDB vector database memory backend.
    
    Stores memory artifacts in ChromaDB with vector embeddings.
    Provides efficient semantic search via ChromaDB's vector operations.
    """

    def __init__(
        self, 
        collection_name: str = "memory_artifacts",
        embedding_provider=None,
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """Initialize ChromaDB memory backend.
        
        Args:
            collection_name: Name of the ChromaDB collection
            embedding_provider: Optional embedding provider for semantic search
            persist_directory: Directory to persist ChromaDB data (for local)
            host: ChromaDB server host (for client mode)
            port: ChromaDB server port (for client mode)
        """
        if chromadb is None:
            raise ImportError("chromadb is required for ChromaDBMemory. Install with: pip install chromadb")
        
        super().__init__(embedding_provider)
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.host = host
        self.port = port
        self._client = None
        self._collection = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure ChromaDB client and collection are set up."""
        if self._initialized:
            return
        
        # Initialize ChromaDB client
        if self.host and self.port:
            # Client mode - connect to ChromaDB server
            self._client = chromadb.HttpClient(host=self.host, port=self.port)
        else:
            # Local mode - persistent or in-memory
            if self.persist_directory:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                self._client = chromadb.Client()
        
        # Get or create collection
        try:
            self._collection = self._client.get_collection(name=self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"description": "Cogency memory artifacts"}
            )
        
        self._initialized = True

    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 10.0
    ) -> MemoryArtifact:
        """Store content in ChromaDB with optional embedding."""
        await self._ensure_initialized()
        
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Prepare metadata for ChromaDB
        chroma_metadata = {
            "memory_type": memory_type.value,
            "tags": json.dumps(tags or []),  # ChromaDB metadata must be strings/numbers
            "metadata": json.dumps(metadata or {}),
            "created_at": artifact.created_at.isoformat(),
            "confidence_score": artifact.confidence_score,
            "access_count": artifact.access_count,
            "last_accessed": artifact.last_accessed.isoformat()
        }
        
        # Generate embedding if provider available
        embedding = None
        if self.embedding_provider:
            try:
                embedding = await self.embedding_provider.embed(content)
            except Exception:
                pass  # Graceful degradation
        
        # Add to ChromaDB
        if embedding:
            self._collection.add(
                ids=[str(artifact.id)],
                documents=[content],
                embeddings=[embedding],
                metadatas=[chroma_metadata]
            )
        else:
            # ChromaDB can generate embeddings automatically if no embedding provided
            self._collection.add(
                ids=[str(artifact.id)],
                documents=[content],
                metadatas=[chroma_metadata]
            )
        
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
        **kwargs
    ) -> List[MemoryArtifact]:
        """Search artifacts using ChromaDB."""
        await self._ensure_initialized()
        
        # Determine search method
        effective_search_type = self._determine_search_type(search_type)
        
        # Build where filter for ChromaDB
        where_filter = {}
        
        if memory_type:
            where_filter["memory_type"] = {"$eq": memory_type.value}
        
        if since:
            where_filter["created_at"] = {"$gte": since}
        
        # Handle tags and metadata filters
        where_document_filter = None
        if tags:
            # Create a filter that checks if any of the provided tags exist in the stored tags
            tag_conditions = []
            for tag in tags:
                tag_conditions.append({"$contains": tag})
            if len(tag_conditions) == 1:
                where_filter["tags"] = tag_conditions[0]
            else:
                where_filter["tags"] = {"$or": tag_conditions}
        
        if effective_search_type == SearchType.SEMANTIC:
            return await self._semantic_search_chroma(query, where_filter, where_document_filter, limit, threshold)
        elif effective_search_type == SearchType.TEXT:
            return await self._text_search_chroma(query, where_filter, where_document_filter, limit)
        elif effective_search_type == SearchType.HYBRID:
            return await self._hybrid_search_chroma(query, where_filter, where_document_filter, limit, threshold)
        else:
            return []

    async def _semantic_search_chroma(self, query: str, where_filter: Dict, where_document_filter: Optional[Dict], limit: int, threshold: float) -> List[MemoryArtifact]:
        """Perform semantic search using ChromaDB vector similarity."""
        query_kwargs = {
            "query_texts": [query],
            "n_results": limit
        }
        
        if where_filter:
            query_kwargs["where"] = where_filter
        
        if where_document_filter:
            query_kwargs["where_document"] = where_document_filter
        
        # Generate embedding if provider available
        if self.embedding_provider:
            try:
                query_embedding = await self.embedding_provider.embed(query)
                if query_embedding:
                    query_kwargs = {
                        "query_embeddings": [query_embedding],
                        "n_results": limit
                    }
                    if where_filter:
                        query_kwargs["where"] = where_filter
                    if where_document_filter:
                        query_kwargs["where_document"] = where_document_filter
            except Exception:
                pass  # Fall back to text-based query
        
        results = self._collection.query(**query_kwargs)
        
        artifacts = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                similarity = 1.0 - distance  # Convert distance to similarity
                
                if similarity >= threshold:
                    artifact = self._result_to_artifact(
                        doc_id, 
                        results["documents"][0][i],
                        results["metadatas"][0][i]
                    )
                    artifact.relevance_score = similarity
                    
                    # Update access stats
                    artifact.access_count += 1
                    artifact.last_accessed = datetime.now(UTC)
                    await self._update_access_stats_chroma(artifact)
                    
                    artifacts.append(artifact)
        
        return artifacts

    async def _text_search_chroma(self, query: str, where_filter: Dict, where_document_filter: Optional[Dict], limit: int) -> List[MemoryArtifact]:
        """Perform text search using ChromaDB document search."""
        # ChromaDB text search using where_document
        text_filter = {"$contains": query}
        
        query_kwargs = {
            "query_texts": [query],
            "n_results": limit,
            "where_document": text_filter
        }
        
        if where_filter:
            query_kwargs["where"] = where_filter
        
        results = self._collection.query(**query_kwargs)
        
        artifacts = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                artifact = self._result_to_artifact(
                    doc_id,
                    results["documents"][0][i],
                    results["metadatas"][0][i]
                )
                
                # Calculate simple text relevance
                content_lower = artifact.content.lower()
                query_lower = query.lower()
                word_matches = sum(1 for word in query_lower.split() if word in content_lower)
                artifact.relevance_score = word_matches / max(1, len(query.split()))
                
                # Update access stats
                artifact.access_count += 1
                artifact.last_accessed = datetime.now(UTC)
                await self._update_access_stats_chroma(artifact)
                
                artifacts.append(artifact)
        
        return artifacts

    async def _hybrid_search_chroma(self, query: str, where_filter: Dict, where_document_filter: Optional[Dict], limit: int, threshold: float) -> List[MemoryArtifact]:
        """Perform hybrid search combining semantic and text results."""
        # Get both search results
        semantic_results = await self._semantic_search_chroma(query, where_filter, where_document_filter, limit, threshold * 0.5)
        text_results = await self._text_search_chroma(query, where_filter, where_document_filter, limit)
        
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
        
        # Sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x.relevance_score * x.decay_score(), reverse=True)
        
        return results[:limit]

    async def _update_access_stats_chroma(self, artifact: MemoryArtifact):
        """Update access statistics for an artifact in ChromaDB."""
        # ChromaDB update requires getting current data and re-adding
        try:
            current = self._collection.get(ids=[str(artifact.id)], include=["metadatas"])
            
            if current["ids"] and current["metadatas"]:
                updated_metadata = current["metadatas"][0].copy()
                updated_metadata["access_count"] = artifact.access_count
                updated_metadata["last_accessed"] = artifact.last_accessed.isoformat()
                
                # Update the document (ChromaDB doesn't have direct update, so we update metadata)
                self._collection.update(
                    ids=[str(artifact.id)],
                    metadatas=[updated_metadata]
                )
        except Exception:
            pass  # Skip if update fails

    def _result_to_artifact(self, doc_id: str, document: str, metadata: Dict) -> MemoryArtifact:
        """Convert ChromaDB result to MemoryArtifact."""
        # Parse metadata back from JSON
        tags = []
        artifact_metadata = {}
        
        if metadata.get("tags"):
            try:
                tags = json.loads(metadata["tags"])
            except json.JSONDecodeError:
                pass
        
        if metadata.get("metadata"):
            try:
                artifact_metadata = json.loads(metadata["metadata"])
            except json.JSONDecodeError:
                pass
        
        artifact = MemoryArtifact(
            id=UUID(doc_id),
            content=document,
            memory_type=MemoryType(metadata.get("memory_type", MemoryType.FACT.value)),
            tags=tags,
            metadata=artifact_metadata,
            confidence_score=float(metadata.get("confidence_score", 1.0)),
            access_count=int(metadata.get("access_count", 0)),
        )
        
        # Parse datetimes
        if metadata.get("created_at"):
            try:
                artifact.created_at = datetime.fromisoformat(metadata["created_at"])
            except ValueError:
                pass
        
        if metadata.get("last_accessed"):
            try:
                artifact.last_accessed = datetime.fromisoformat(metadata["last_accessed"])
            except ValueError:
                pass
        
        return artifact

    def _determine_search_type(self, search_type: SearchType) -> SearchType:
        """Determine effective search type based on availability."""
        if search_type == SearchType.AUTO:
            # ChromaDB supports both semantic and text, prefer semantic if embedding provider available
            return SearchType.SEMANTIC if self.embedding_provider else SearchType.TEXT
        return search_type

    async def forget(self, artifact_id: UUID) -> bool:
        """Remove artifact from ChromaDB."""
        await self._ensure_initialized()
        
        try:
            self._collection.delete(ids=[str(artifact_id)])
            return True
        except Exception:
            return False

    async def clear(self) -> None:
        """Clear all artifacts from ChromaDB."""
        await self._ensure_initialized()
        
        try:
            # Delete collection and recreate
            self._client.delete_collection(name=self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"description": "Cogency memory artifacts"}
            )
        except Exception:
            pass

    async def close(self):
        """Clean up ChromaDB resources."""
        # ChromaDB client doesn't need explicit cleanup
        self._client = None
        self._collection = None
        self._initialized = False

    def _get_chromadb_stats(self) -> Dict[str, Any]:
        """Get ChromaDB-specific stats."""
        stats = {
            "backend": "chromadb",
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "host": self.host,
            "port": self.port
        }
        
        if self._collection:
            try:
                count = self._collection.count()
                stats["count"] = count
            except Exception:
                pass
        
        return stats

    async def inspect(self) -> Dict[str, Any]:
        """Enhanced inspect with ChromaDB stats."""
        base_stats = await super().inspect()
        base_stats.update(self._get_chromadb_stats())
        return base_stats