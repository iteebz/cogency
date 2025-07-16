"""ChromaDB storage implementation."""
import json
import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base import BaseStorage
from ..base import MemoryArtifact, MemoryType

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


class ChromaDBStorage(BaseStorage):
    """ChromaDB storage implementation."""
    
    def __init__(
        self, 
        collection_name: str = "memory_artifacts",
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None
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
    
    async def clear(self) -> None:
        await self._ensure_initialized()
        try:
            self._client.delete_collection(name=self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"description": "Cogency memory artifacts"}
            )
        except Exception:
            pass
    
    def _result_to_artifact(self, doc_id: str, document: str, metadata: Dict) -> MemoryArtifact:
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