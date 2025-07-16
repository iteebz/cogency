"""Memory tools for Cogency agents using BaseMemory."""
from typing import Any, Dict, List, Optional
import json

from .base import BaseTool
from .registry import tool
from ..memory.base import BaseMemory


@tool
class MemorizeTool(BaseTool):
    """Tool for storing content in agent memory."""

    def __init__(self, memory: BaseMemory):
        super().__init__(
            name="memorize",
            description="Store important information the user wants remembered for future conversations (explicit user request to remember something)"
        )
        self.memory = memory

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Store content in memory with smart auto-tagging."""
        content = kwargs.get("content")
        if not content:
            return {"error": "content parameter is required"}
        
        tags = kwargs.get("tags", [])
        metadata = kwargs.get("metadata", {})
        
        # Extract user_id from context if available
        context = kwargs.get("_context")
        user_id = getattr(context, 'user_id', 'default') if context else 'default'
        
        # Smart auto-tagging if no tags provided
        if not tags and hasattr(self.memory, 'should_store'):
            should_store, category = self.memory.should_store(content)
            if category:
                tags = [category]
        
        try:
            artifact = await self.memory.memorize(content, tags=tags, metadata=metadata, user_id=user_id)
            return {
                "success": True,
                "artifact_id": str(artifact.id),
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "tags": tags
            }
        except Exception as e:
            return {"error": f"Failed to memorize content: {str(e)}"}

    def get_schema(self) -> str:
        return "memorize(content='text to remember', tags=['tag1', 'tag2'])"

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls."""
        return [
            'memorize(content="Remember that I prefer working in quiet environments", tags=["preferences"])',
            'memorize(content="I have ADHD and work as a software engineer", tags=["personal"])',
            'memorize(content="Project deadline is next Friday", tags=["work"])'
        ]


@tool
class RecallTool(BaseTool):
    """Tool for retrieving content from agent memory."""

    def __init__(self, memory: BaseMemory):
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
            artifacts = await self.memory.recall(query, limit=limit, tags=tags if tags else None, user_id=user_id)
            
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