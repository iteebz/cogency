"""Document retrieval tool - semantic search using VectorStore backends."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from resilient_result import Result

from cogency.storage.vector import FileStore, VectorStore
from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class RetrievalArgs:
    query: str
    top_k: int = 5
    threshold: Optional[float] = None
    filters: Optional[Dict[str, Any]] = None


@tool
class Retrieval(Tool):
    """Semantic document search using VectorStore backends.

    Requires pre-computed embeddings - does not embed documents on-demand.
    Use embedding scripts to generate embeddings files before using this tool.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embeddings_path: str = "./embeddings.json",
        embed_model: str = "openai",
        top_k: int = 5,
    ):
        super().__init__(
            name="retrieval",
            description="Search documents using semantic similarity via vector store backends",
            schema="retrieval(query: str, top_k: int = 5, threshold: float = None, filters: dict = None)",
            emoji="📚",
            args=RetrievalArgs,
            examples=[
                '{"name": "retrieval", "args": {"query": "user authentication methods"}}',
                '{"name": "retrieval", "args": {"query": "API rate limiting", "top_k": 10}}',
                '{"name": "retrieval", "args": {"query": "deployment", "threshold": 0.7}}',
            ],
            rules=[
                'Use JSON format: {"name": "retrieval", "args": {"query": "...", "top_k": 5}}',
                "Use specific queries for better semantic matching",
                "Requires pre-computed embeddings - does not embed documents on-demand",
                "Higher top_k returns more results but may include less relevant content",
                "Use threshold to filter low-similarity results",
            ],
        )

        # Vector store configuration
        self.vector_store = vector_store or FileStore(embeddings_path)
        self.embed_model = embed_model
        self.default_top_k = top_k

        # Lazy-loaded embedder for query processing
        self._embedder = None

        # Formatting templates
        self.arg_key = "query"
        self.human_template = "Found {total_results} relevant documents:\n{results_summary}"
        self.agent_template = "Retrieved {total_results} documents:\n{results_summary}"

    async def run(
        self,
        query: str,
        top_k: int = None,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Search documents using vector store backend."""
        if not query or not query.strip():
            return Result.fail("Search query cannot be empty")

        query = query.strip()
        k = top_k if top_k is not None else self.default_top_k

        # Validate parameters
        if k <= 0:
            return Result.fail("top_k must be positive")
        if k > 50:
            k = 50  # Cap at reasonable limit

        try:
            # Get query embedding
            if self._embedder is None:
                self._embedder = await self._get_embedder()

            embed_result = await self._embedder.embed([query])
            if embed_result.failure:
                return Result.fail(f"Query embedding failed: {embed_result.error}")

            query_embedding = embed_result.data[0]

            # Search using vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding, top_k=k, filters=filters, threshold=threshold
            )

            if not results:
                return Result.ok(
                    {
                        "results": [],
                        "query": query,
                        "total_results": 0,
                        "message": f"No relevant content found for '{query}'",
                        "results_summary": "No relevant content found",
                    }
                )

            # Format results for tool output
            formatted_results = []
            results_summary = []

            for i, result in enumerate(results, 1):
                # Extract content and metadata
                content = result.get("content", "")
                similarity = result.get("similarity", 0.0)
                metadata = result.get("metadata", {})
                source = metadata.get("source", f"Document {i}")

                formatted_result = {
                    "content": content,
                    "source": source,
                    "similarity_score": similarity,
                    "metadata": metadata,
                }
                formatted_results.append(formatted_result)

                # Create summary (top 3 for display)
                if i <= 3:
                    preview = content[:150] + "..." if len(content) > 150 else content
                    results_summary.append(f"{i}. {source} (sim: {similarity:.3f}): {preview}")

            return Result.ok(
                {
                    "results": formatted_results,
                    "query": query,
                    "total_results": len(formatted_results),
                    "message": f"Found {len(formatted_results)} relevant documents for '{query}'",
                    "results_summary": "\n".join(results_summary),
                }
            )

        except Exception as e:
            logger.error(f"Retrieval search failed for query '{query}': {e}")
            return Result.fail(f"Document search failed: {str(e)}")

    async def _get_embedder(self):
        """Get the configured embedding provider for query processing."""
        from cogency.providers.setup import _setup_embed

        embed_class = _setup_embed(self.embed_model)

        # For Nomic, use search_query task type
        if self.embed_model == "nomic":
            return embed_class(task_type="search_query")
        else:
            return embed_class()
