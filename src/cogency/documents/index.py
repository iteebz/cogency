"""Document indexing utilities."""

import json
from pathlib import Path

from resilient_result import Result


async def index(documents: list[dict], embedder, output_path: str) -> Result:
    """Create searchable document index with embeddings."""
    try:
        # Extract content for embedding
        contents = [doc.get("content", "") for doc in documents]

        # Generate embeddings
        embed_result = await embedder.embed(contents)
        if embed_result.failure:
            return Result.fail(f"Embedding generation failed: {embed_result.error}")

        embeddings = embed_result.unwrap()

        # Create index structure
        index_data = {
            "documents": documents,
            "embeddings": embeddings,
            "metadata": {
                "document_count": len(documents),
                "embedding_dimension": len(embeddings[0]) if embeddings else 0,
                "created_at": str(Path().cwd()),  # Placeholder for timestamp
            },
        }

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(index_data, f, indent=2)

        return Result.ok(
            {
                "indexed_documents": len(documents),
                "output_path": str(output_file),
                "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            }
        )

    except Exception as e:
        return Result.fail(f"Document indexing failed: {str(e)}")


def load(directory: str, extensions: list[str] = None) -> list[dict]:
    """Load documents from directory for indexing."""
    if extensions is None:
        extensions = [".txt", ".md", ".py", ".js", ".json"]

    documents = []
    directory_path = Path(directory)

    if not directory_path.exists():
        return documents

    for file_path in directory_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in extensions:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                documents.append(
                    {
                        "content": content,
                        "metadata": {
                            "file_path": str(file_path),
                            "file_name": file_path.name,
                            "file_type": file_path.suffix,
                            "file_size": len(content),
                        },
                    }
                )
            except Exception:
                # Skip files that can't be read
                continue

    return documents


async def index_dir(
    directory: str, embedder, output_path: str, extensions: list[str] = None
) -> Result:
    """Index all documents in a directory."""
    try:
        # Load documents
        documents = load(directory, extensions)

        if not documents:
            return Result.fail(f"No documents found in directory: {directory}")

        # Create index
        return await index(documents, embedder, output_path)

    except Exception as e:
        return Result.fail(f"Directory indexing failed: {str(e)}")
