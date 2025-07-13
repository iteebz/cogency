"""Memory tools for Cogency agents using BaseMemory."""
from typing import Any, Dict, List, Optional
import json

from ..tools.base import BaseTool
from ..tools.registry import tool
from .base import BaseMemory


@tool
class MemorizeTool(BaseTool):
    """Tool for storing content in agent memory."""

    def __init__(self, memory: BaseMemory):
        super().__init__(
            name="memorize",
            description="Store information in memory for later recall"
        )
        self.memory = memory

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Store content in memory.
        
        Expected kwargs:
            content (str): The content to memorize
            tags (List[str], optional): Tags for categorization
            metadata (Dict[str, Any], optional): Additional metadata
        """
        content = kwargs.get("content")
        if not content:
            return {"error": "content parameter is required"}
        
        tags = kwargs.get("tags", [])
        metadata = kwargs.get("metadata", {})
        
        try:
            artifact = await self.memory.memorize(content, tags=tags, metadata=metadata)
            return {
                "success": True,
                "artifact_id": str(artifact.id),
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "tags": tags
            }
        except Exception as e:
            return {"error": f"Failed to memorize content: {str(e)}"}

    def get_schema(self) -> str:
        """Return the tool schema for LLM formatting."""
        return json.dumps({
            "name": "memorize",
            "description": "Store information in memory for later recall",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to store in memory"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for categorization"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata dictionary"
                    }
                },
                "required": ["content"]
            }
        })

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls."""
        return [
            'memorize(content="Important meeting notes from client call", tags=["meeting", "client"])',
            'memorize(content="API endpoint returns user data", tags=["api", "documentation"])',
            'memorize(content="Error: connection timeout at line 42", tags=["error", "debugging"])'
        ]


@tool
class RecallTool(BaseTool):
    """Tool for retrieving content from agent memory."""

    def __init__(self, memory: BaseMemory):
        super().__init__(
            name="recall",
            description="Search and retrieve information from memory"
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
        
        try:
            artifacts = await self.memory.recall(query, limit=limit, tags=tags if tags else None)
            
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
        """Return the tool schema for LLM formatting."""
        return json.dumps({
            "name": "recall",
            "description": "Search and retrieve information from memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to match against stored content"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter results by tags"
                    }
                },
                "required": ["query"]
            }
        })

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls."""
        return [
            'recall(query="meeting notes with client")',
            'recall(query="API documentation", limit=5)',
            'recall(query="error debugging", tags=["error"])'
        ]