"""Recall tool for Cogency agents using BaseMemory."""
from typing import Any, Dict, List, Optional
import json

from .base import BaseTool
from .registry import tool
from ..memory.core import MemoryBackend


@tool
class Recall(BaseTool):
    """Tool for retrieving content from agent memory."""

    def __init__(self, memory: MemoryBackend):
        super().__init__(
            name="recall",
            description="Search and retrieve previously stored information when user asks about their personal details, work, preferences, or past conversations"
        )
        self.memory = memory

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Retrieve content from memory.
        
        Expected kwargs:
            query (str): Search query
            limit (int, optional): Maximum number of results
            tags (List[str], optional): Filter by tags
        """
        query = kwargs.get("query")
        if not query:
            return {"error": "query parameter is required"}
        
        limit = kwargs.get("limit")
        tags = kwargs.get("tags", [])
        
        # Extract user_id from context if available
        context = kwargs.get("_context")
        user_id = getattr(context, 'user_id', 'default') if context else 'default'
        
        try:
            artifacts = await self.memory.read(query=query, limit=limit, tags=tags if tags else None, user_id=user_id)
            
            results = []
            for artifact in artifacts:
                results.append({
                    "id": str(artifact.id),
                    "content": artifact.content,
                    "tags": artifact.tags,
                    "created_at": artifact.created_at.isoformat(),
                    "metadata": artifact.metadata
                })
            
            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results
            }
        except Exception as e:
            return {"error": f"Failed to recall content: {str(e)}"}

    def get_schema(self) -> str:
        return "recall(query='search terms', limit=5, tags=['tag1'])"

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls."""
        return [
            'recall(query="my work situation")',
            'recall(query="personal information about me")',
            'recall(query="my preferences", tags=["preferences"])'
        ]