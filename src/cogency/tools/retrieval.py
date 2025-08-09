"""Document retrieval tool - semantic search with lazy indexing and intelligent defaults."""

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class RetrievalArgs:
    query: str
    top_k: int = 3


@tool
class Retrieval(Tool):
    """Semantic document search using existing embedding infrastructure."""

    def __init__(
        self,
        path: str = "./docs",
        embed_model: str = "openai",
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        top_k: int = 3,
    ):
        super().__init__(
            name="retrieval",
            description="Search documents and knowledge base for relevant information using semantic similarity",
            schema="retrieval(query: str, top_k: int = 3)",
            emoji="📚",
            args=RetrievalArgs,
            examples=[
                '{"name": "retrieval", "args": {"query": "user authentication methods"}}',
                '{"name": "retrieval", "args": {"query": "API rate limiting", "top_k": 5}}',
                '{"name": "retrieval", "args": {"query": "deployment configuration"}}',
            ],
            rules=[
                'Use JSON format: {"name": "retrieval", "args": {"query": "...", "top_k": 3}}',
                "Use specific queries for better semantic matching",
                "Higher top_k returns more results but may include less relevant content",
            ],
        )

        # Configuration
        self.path = Path(path)
        self.embed_model = embed_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.default_top_k = top_k

        # Lazy-loaded components
        self._embedder = None
        self._index = None
        self._content_hash = None

        # Formatting templates
        self.arg_key = "query"
        self.human_template = "Found {total_results} relevant documents:\n{results_summary}"
        self.agent_template = "Retrieved {total_results} documents:\n{results_summary}"

    async def run(self, query: str, top_k: int = None, **kwargs) -> Dict[str, Any]:
        """Search documents for relevant content."""
        if not query or not query.strip():
            return Result.fail("Search query cannot be empty")

        query = query.strip()
        k = top_k if top_k is not None else self.default_top_k

        # Validate k
        if k <= 0:
            return Result.fail("top_k must be positive")
        if k > 20:
            k = 20  # Cap at reasonable limit

        try:
            # Ensure index is built
            await self._ensure_index()

            if not self._index:
                return Result.ok(
                    {
                        "results": [],
                        "query": query,
                        "total_results": 0,
                        "message": f"No documents found in {self.path}",
                        "results_summary": "No documents available for search",
                    }
                )

            # Perform semantic search
            results = await self._search(query, k)

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

            # Format results summary for context
            results_summary = []
            for i, result in enumerate(results[:3], 1):  # Top 3 for summary
                preview = (
                    result["content"][:200] + "..."
                    if len(result["content"]) > 200
                    else result["content"]
                )
                results_summary.append(f"{i}. {result['source']}: {preview}")

            return Result.ok(
                {
                    "results": results,
                    "query": query,
                    "total_results": len(results),
                    "message": f"Found {len(results)} relevant documents for '{query}'",
                    "results_summary": "\n".join(results_summary),
                }
            )

        except Exception as e:
            logger.error(f"Retrieval search failed for query '{query}': {e}")
            return Result.fail(f"Document search failed: {str(e)}")

    async def _ensure_index(self):
        """Ensure the document index is built and up-to-date."""
        if not self.path.exists():
            logger.warning(f"Document path does not exist: {self.path}")
            return

        # Check if index needs rebuilding
        current_hash = self._compute_content_hash()
        if self._index is not None and self._content_hash == current_hash:
            return  # Index is up-to-date

        logger.info(f"Building document index for {self.path}")
        await self._build_index()
        self._content_hash = current_hash

    def _compute_content_hash(self) -> str:
        """Compute hash of all document content for change detection."""
        if not self.path.exists():
            return ""

        hasher = hashlib.md5()
        for file_path in sorted(self._discover_documents()):
            hasher.update(str(file_path).encode())
            try:
                hasher.update(file_path.read_bytes())
            except Exception:
                continue  # Skip files that can't be read

        return hasher.hexdigest()

    def _discover_documents(self) -> List[Path]:
        """Discover all readable documents in the path."""
        if not self.path.exists():
            return []

        supported_extensions = {
            ".txt",
            ".md",
            ".rst",
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yaml",
            ".yml",
        }
        documents = []

        if self.path.is_file():
            if self.path.suffix.lower() in supported_extensions:
                documents.append(self.path)
        else:
            for ext in supported_extensions:
                documents.extend(self.path.rglob(f"*{ext}"))

        return sorted(documents)

    async def _build_index(self):
        """Build the document index with embeddings."""
        documents = self._discover_documents()
        if not documents:
            self._index = None
            return

        # Load embedder
        if self._embedder is None:
            self._embedder = await self._get_embedder()

        # Process documents into chunks
        chunks = []
        for doc_path in documents:
            try:
                content = doc_path.read_text(encoding="utf-8", errors="ignore")
                doc_chunks = self._chunk_document(content, str(doc_path.relative_to(self.path)))
                chunks.extend(doc_chunks)
            except Exception as e:
                logger.warning(f"Failed to process document {doc_path}: {e}")
                continue

        if not chunks:
            self._index = None
            return

        # Generate embeddings
        texts = [chunk["content"] for chunk in chunks]
        try:
            result = self._embedder.embed(texts)
            if result.failure:
                logger.error(f"Embedding generation failed: {result.error}")
                self._index = None
                return
            embeddings = result.data
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            self._index = None
            return

        # Build simple in-memory index
        self._index = {
            "chunks": chunks,
            "embeddings": np.array(embeddings),
        }

        logger.info(f"Built index with {len(chunks)} chunks from {len(documents)} documents")

    def _chunk_document(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Split document into overlapping chunks."""
        if not content.strip():
            return []

        chunks = []
        start = 0

        while start < len(content):
            end = start + self.chunk_size
            chunk_text = content[start:end]

            # Try to break at word boundaries
            if end < len(content):
                last_space = chunk_text.rfind(" ")
                if last_space > self.chunk_size * 0.8:  # Only if we don't lose too much
                    chunk_text = chunk_text[:last_space]
                    end = start + last_space

            if chunk_text.strip():
                chunks.append(
                    {
                        "content": chunk_text.strip(),
                        "source": source,
                        "start": start,
                        "end": end,
                    }
                )

            start = end - self.chunk_overlap
            if start >= len(content):
                break

        return chunks

    async def _search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic search against the index."""
        if not self._index:
            return []

        # Get query embedding
        result = self._embedder.embed([query])
        if result.failure:
            return []
        query_embedding = result.data
        query_vector = np.array(query_embedding[0])

        # Compute similarities
        embeddings = self._index["embeddings"]
        similarities = np.dot(embeddings, query_vector) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vector)
        )

        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            chunk = self._index["chunks"][idx]
            similarity_score = float(similarities[idx])

            # Only return results with reasonable similarity
            if similarity_score > 0.1:  # Threshold for relevance
                results.append(
                    {
                        "content": chunk["content"],
                        "source": chunk["source"],
                        "similarity_score": similarity_score,
                        "start": chunk["start"],
                        "end": chunk["end"],
                    }
                )

        return results

    async def _get_embedder(self):
        """Get the configured embedding provider using canonical setup."""
        from cogency.providers.setup import _setup_embed

        embed_class = _setup_embed(self.embed_model)
        return embed_class()
