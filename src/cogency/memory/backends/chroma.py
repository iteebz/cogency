"""ChromaDB storage implementation."""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base import BaseBackend
from ..core import Memory, MemoryType, SearchType

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


class ChromaBackend(BaseBackend):
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
        super().__init__(embedding_provider)
    
    async def _ready(self):
        """Initialize ChromaDB client and collection."""
        if self._collection:
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
    
    def _has_search(self, search_type: SearchType) -> bool:
        """ChromaDB supports semantic search only."""
        return search_type in [SearchType.SEMANTIC, SearchType.AUTO] and self.embedding_provider
    
    async def _search(
        self, query: str, search_type: SearchType, limit: int, threshold: float,
        tags: Optional[List[str]], memory_type: Optional[MemoryType], 
        filters: Optional[Dict[str, Any]], **kwargs
    ) -> List[Memory]:
        """Native ChromaDB semantic search."""
        if search_type == SearchType.TEXT:
            raise NotImplementedError("Text search not supported by ChromaDB backend")
        if search_type == SearchType.HYBRID:
            raise NotImplementedError("Hybrid search not supported by ChromaDB backend")
        
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # Build where filter
        where_filter = None
        if tags or memory_type or filters:
            conditions = []
            if tags:
                conditions.append({"tags": {"$in": tags}})
            if memory_type:
                conditions.append({"memory_type": memory_type.value})
            if filters:
                conditions.extend([{k: v} for k, v in filters.items()])
            
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
    
    async def _store(self, artifact: Memory, embedding: Optional[List[float]], **kwargs) -> None:
        """Store artifact in ChromaDB."""
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
    
    async def _read_by_id(self, artifact_id: UUID) -> List[Memory]:
        """Read single artifact by ID."""
        try:
            results = self._collection.get(ids=[str(artifact_id)], include=["documents", "metadatas"])
            if results["ids"] and results["ids"][0]:
                artifact = self._result_to_artifact(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0]
                )
                return [artifact]
        except Exception:
            pass
        return []
    
    async def _read_filtered(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Memory]:
        """Read filtered artifacts."""
        # Build where filter
        where_filter = {}
        if memory_type:
            where_filter["memory_type"] = {"$eq": memory_type.value}
        if filters and filters.get('since'):
            where_filter["created_at"] = {"$gte": filters['since']}
        if filters and filters.get('metadata_filter'):
            where_filter.update(filters['metadata_filter'])
        
        # Handle tags filter
        if tags:
            tag_conditions = []
            for tag in tags:
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
    
    async def _update_artifact(self, artifact_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update artifact in ChromaDB."""
        try:
            # ChromaDB doesn't support direct updates, we need to delete and re-add
            # First, get the existing artifact
            results = self._collection.get(ids=[str(artifact_id)], include=["documents", "metadatas", "embeddings"])
            if not results["ids"] or not results["ids"][0]:
                return False
            
            # Extract current data
            current_metadata = results["metadatas"][0]
            current_content = results["documents"][0]
            current_embedding = results["embeddings"][0] if results["embeddings"] else None
            
            # Apply updates
            for key, value in updates.items():
                if key == 'tags' and isinstance(value, list):
                    current_metadata['tags'] = json.dumps(value)
                elif key == 'metadata' and isinstance(value, dict):
                    current_metadata['metadata'] = json.dumps(value)
                elif key in ['access_count', 'confidence_score']:
                    current_metadata[key] = value
                elif key in ['last_accessed']:
                    current_metadata[key] = value.isoformat() if hasattr(value, 'isoformat') else value
            
            # Delete old version
            self._collection.delete(ids=[str(artifact_id)])
            
            # Re-add with updates
            if current_embedding:
                self._collection.add(
                    ids=[str(artifact_id)],
                    documents=[current_content],
                    embeddings=[current_embedding],
                    metadatas=[current_metadata]
                )
            else:
                self._collection.add(
                    ids=[str(artifact_id)],
                    documents=[current_content],
                    metadatas=[current_metadata]
                )
            
            return True
        except Exception:
            return False
    
    async def _delete_all(self) -> bool:
        """Delete all artifacts."""
        try:
            self._collection.delete()
            return True
        except Exception:
            return False
    
    async def _delete_by_id(self, artifact_id: UUID) -> bool:
        """Delete single artifact by ID."""
        try:
            self._collection.delete(ids=[str(artifact_id)])
            return True
        except Exception:
            return False
    
    async def _delete_by_filters(self, tags: Optional[List[str]], filters: Optional[Dict[str, Any]]) -> bool:
        """Delete artifacts by filters."""
        where_filter = None
        conditions = []
        if tags:
            conditions.append({"tags": {"$in": tags}})
        if filters:
            conditions.extend([{k: v} for k, v in filters.items()])
        
        if len(conditions) == 1:
            where_filter = conditions[0]
        else:
            where_filter = {"$and": conditions}
        
        try:
            self._collection.delete(where=where_filter)
            return True
        except Exception:
            return False
    
    def _result_to_artifact(self, doc_id: str, document: str, metadata: Dict) -> Memory:
        """Convert ChromaDB result to Memory."""
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
        
        artifact = Memory(
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
        def _get_stats():
            count = self._collection.count()
            return {
                'total_memories': count,
                'backend': 'chromadb',
                'collection_name': self.collection_name
            }
        
        return self._stats(_get_stats, 'chromadb')