"""ChromaDB storage implementation."""
import json
import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..core import MemoryBackend, MemoryArtifact, MemoryType, SearchType

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


class ChromaBackend(MemoryBackend):
    """ChromaDB storage implementation."""
    
    def __init__(
        self, 
        collection_name: str = "memory_artifacts",
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        embedding_provider=None
    ):
        if chromadb is None:
            raise ImportError("ChromaDB support not installed. Use `pip install cogency[chromadb]`")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.host = host
        self.port = port
        self._client = None
        self._collection = None
        self._initialized = False
        super().__init__(embedding_provider)
    
    async def _ensure_initialized(self):
        if self._initialized:
            return
        
        # Initialize ChromaDB client
        if self.host and self.port:
            self._client = chromadb.HttpClient(host=self.host, port=self.port)
        else:
            if self.persist_directory:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                self._client = chromadb.Client()
        
        # Get or create collection
        try:
            self._collection = self._client.get_collection(name=self.collection_name)
        except Exception:
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
        **kwargs
    ) -> MemoryArtifact:
        """Store new content in memory."""
        if not self.embedding_provider:
            raise ValueError("Embedding provider required for ChromaDB backend")
            
        artifact = MemoryArtifact(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        embedding = None
        if self.embedding_provider:
            try:
                embedding = await self.embedding_provider.embed_text(content)
            except Exception:
                pass
        
        await self.store(artifact, embedding, **kwargs)
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
        **kwargs
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content from memory."""
        # ChromaDB only supports semantic search
        if search_type == SearchType.TEXT:
            raise NotImplementedError("Text search not supported by ChromaDB backend")
        if search_type == SearchType.HYBRID:
            raise NotImplementedError("Hybrid search not supported by ChromaDB backend")
            
        await self._ensure_initialized()
        
        if not self.embedding_provider:
            raise ValueError("Embedding provider required for semantic search")
            
        # Get query embedding
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # Build where filter
        where_filter = None
        if tags or memory_type or metadata_filter:
            conditions = []
            if tags:
                conditions.append({"tags": {"$in": tags}})
            if memory_type:
                conditions.append({"memory_type": memory_type.value})
            if metadata_filter:
                conditions.extend([{k: v} for k, v in metadata_filter.items()])
            
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}
        
        # Query ChromaDB
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if where_filter:
            query_kwargs["where"] = where_filter
            
        results = self._collection.query(**query_kwargs)
        
        # Convert to artifacts
        artifacts = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB uses distance (lower = better), convert to similarity
                distance = results["distances"][0][i]
                similarity = 1.0 - distance
                
                # Filter by threshold
                if similarity >= threshold:
                    artifact = self._result_to_artifact(
                        doc_id,
                        results["documents"][0][i],
                        results["metadatas"][0][i]
                    )
                    artifact.relevance_score = similarity
                    artifacts.append(artifact)
        
        return artifacts
    
    async def forget(self, artifact_id: UUID = None, tags: Optional[List[str]] = None, metadata_filter: Optional[Dict[str, Any]] = None) -> bool:
        """Remove artifact(s) from memory."""
        await self._ensure_initialized()
        
        if not artifact_id and not tags and not metadata_filter:
            raise ValueError("Must provide either artifact_id or filters (tags/metadata_filter)")
        
        if artifact_id:
            return await self.delete(artifact_id)
        
        # Delete by filters
        where_filter = None
        conditions = []
        if tags:
            conditions.append({"tags": {"$in": tags}})
        if metadata_filter:
            conditions.extend([{k: v} for k, v in metadata_filter.items()])
        
        if len(conditions) == 1:
            where_filter = conditions[0]
        else:
            where_filter = {"$and": conditions}
        
        try:
            self._collection.delete(where=where_filter)
            return True
        except Exception:
            return False
    
    async def store(self, artifact: MemoryArtifact, embedding: Optional[List[float]], **kwargs) -> None:
        await self._ensure_initialized()
        
        metadata = {
            "memory_type": artifact.memory_type.value,
            "tags": json.dumps(artifact.tags),
            "metadata": json.dumps(artifact.metadata),
            "created_at": artifact.created_at.isoformat(),
            "confidence_score": artifact.confidence_score,
            "access_count": artifact.access_count,
            "last_accessed": artifact.last_accessed.isoformat()
        }
        
        if embedding:
            self._collection.add(
                ids=[str(artifact.id)],
                documents=[artifact.content],
                embeddings=[embedding],
                metadatas=[metadata]
            )
        else:
            self._collection.add(
                ids=[str(artifact.id)],
                documents=[artifact.content],
                metadatas=[metadata]
            )
    
    async def load_all(self, **filters) -> List[MemoryArtifact]:
        await self._ensure_initialized()
        
        # Build where filter
        where_filter = {}
        if filters.get('memory_type'):
            where_filter["memory_type"] = {"$eq": filters['memory_type'].value}
        if filters.get('since'):
            where_filter["created_at"] = {"$gte": filters['since']}
        
        # Handle tags filter
        if filters.get('tags'):
            tag_conditions = []
            for tag in filters['tags']:
                tag_conditions.append({"$contains": tag})
            if len(tag_conditions) == 1:
                where_filter["tags"] = tag_conditions[0]
            else:
                where_filter["tags"] = {"$or": tag_conditions}
        
        query_kwargs = {"where": where_filter} if where_filter else {}
        
        try:
            results = self._collection.get(include=["documents", "metadatas"], **query_kwargs)
        except Exception:
            # Fallback: get all and filter manually
            results = self._collection.get(include=["documents", "metadatas"])
        
        artifacts = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                artifact = self._result_to_artifact(
                    doc_id,
                    results["documents"][i],
                    results["metadatas"][i]
                )
                artifacts.append(artifact)
        
        return artifacts
    
    async def get_embedding(self, artifact_id: UUID) -> Optional[List[float]]:
        await self._ensure_initialized()
        try:
            results = self._collection.get(ids=[str(artifact_id)], include=["embeddings"])
            if results["embeddings"] and results["embeddings"][0]:
                return results["embeddings"][0]
        except Exception:
            pass
        return None
    
    async def delete(self, artifact_id: UUID) -> bool:
        await self._ensure_initialized()
        try:
            self._collection.delete(ids=[str(artifact_id)])
            return True
        except Exception:
            return False
    
    async def clear(self) -> bool:
        await self._ensure_initialized()
        try:
            self._collection.delete()
            return True
        except Exception:
            return False
    
    def _result_to_artifact(self, doc_id: str, document: str, metadata: Dict) -> MemoryArtifact:
        tags = []
        artifact_metadata = {}
        
        if metadata.get("tags"):
            try:
                if isinstance(metadata["tags"], str):
                    tags = json.loads(metadata["tags"])
                else:
                    tags = metadata["tags"]  # Already a list
            except (json.JSONDecodeError, TypeError):
                pass
        
        if metadata.get("metadata"):
            try:
                if isinstance(metadata["metadata"], str):
                    artifact_metadata = json.loads(metadata["metadata"])
                else:
                    artifact_metadata = metadata["metadata"]  # Already a dict
            except (json.JSONDecodeError, TypeError):
                pass
        
        try:
            artifact_id = UUID(doc_id)
        except ValueError:
            # For test compatibility, generate a UUID from the string
            from uuid import uuid5, NAMESPACE_DNS
            artifact_id = uuid5(NAMESPACE_DNS, doc_id)
        
        artifact = MemoryArtifact(
            id=artifact_id,
            content=document,
            memory_type=MemoryType(metadata.get("memory_type", MemoryType.FACT.value)),
            tags=tags,
            metadata=artifact_metadata,
            confidence_score=float(metadata.get("confidence_score", 1.0)),
            access_count=int(metadata.get("access_count", 0))
        )
        
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
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        await self._ensure_initialized()
        
        try:
            count = self._collection.count()
            return {
                'total_memories': count,
                'backend': 'chromadb',
                'collection_name': self.collection_name
            }
        except Exception:
            return {
                'total_memories': 0,
                'backend': 'chromadb',
                'collection_name': self.collection_name
            }