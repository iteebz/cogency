"""Archive memory - knowledge artifact preservation.

Handles knowledge distillation from conversations:
- Extract valuable knowledge from conversation history
- Merge knowledge with existing topic documents
- Store refined knowledge artifacts for future retrieval
"""

from .core import archive

__all__ = ["archive"]
