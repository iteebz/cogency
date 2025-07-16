"""Zero-ceremony memory test utilities."""

from datetime import datetime, timezone
from cogency.memory.base import MemoryType, MemoryArtifact


def create_artifact(id="test", content="test content", **kwargs):
    """Create test artifact with sane defaults."""
    return MemoryArtifact(
        id=id,
        content=content,
        memory_type=kwargs.get('memory_type', MemoryType.FACT),
        tags=kwargs.get('tags', ['test']),
        metadata=kwargs.get('metadata', {}),
        created_at=kwargs.get('created_at', datetime.now(timezone.utc)),
        access_count=kwargs.get('access_count', 0),
        last_accessed=kwargs.get('last_accessed', datetime.now(timezone.utc)),
        user_id=kwargs.get('user_id', 'test-user')
    )


def mock_vector_response(scores=[0.9, 0.8], contents=None):
    """Create mock vector DB response."""
    if contents is None:
        contents = [f"Content {i+1}" for i in range(len(scores))]
    
    return {
        'matches': [
            {
                'id': f'id-{i+1}',
                'score': score,
                'metadata': {
                    'content': content,
                    'memory_type': 'fact',
                    'tags': ['test'],
                    'created_at': '2024-01-01T00:00:00+00:00',
                    'access_count': 0,
                    'last_accessed': '2024-01-01T00:00:00+00:00'
                }
            }
            for i, (score, content) in enumerate(zip(scores, contents))
        ]
    }


async def crud_memorize(backend, content="test", **kwargs):
    """Standard memorize test."""
    return await backend.memorize(
        content=content,
        memory_type=kwargs.get('memory_type', MemoryType.FACT),
        tags=kwargs.get('tags', ['test']),
        metadata=kwargs.get('metadata', {})
    )


async def crud_recall(backend, query="test", **kwargs):
    """Standard recall test."""
    return await backend.recall(
        query=query,
        limit=kwargs.get('limit', 5),
        threshold=kwargs.get('threshold', 0.7)
    )


async def crud_forget(backend, artifact_id="test-id"):
    """Standard forget test."""
    return await backend.forget(artifact_id=artifact_id)


async def crud_clear(backend):
    """Standard clear test."""
    return await backend.clear()


def assert_artifact(artifact, content=None, memory_type=None):
    """Assert artifact structure and optionally values."""
    assert hasattr(artifact, 'id')
    assert hasattr(artifact, 'content')
    assert hasattr(artifact, 'memory_type')
    
    if content:
        assert artifact.content == content
    if memory_type:
        assert artifact.memory_type == memory_type