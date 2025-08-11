"""Archive memory - knowledge artifact preservation.

Handles knowledge distillation from conversations:
- Extract valuable knowledge from conversation history
- Merge knowledge with existing topic documents
- Store refined knowledge artifacts for future retrieval
"""

from . import search, storage
from .extract import archive
from .types import TopicArtifact

# Simplified interface - no more big classes
__all__ = ["archive", "TopicArtifact", "storage", "search"]
