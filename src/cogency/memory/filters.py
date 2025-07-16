"""Memory filtering utilities to eliminate duplication."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from .base import MemoryType


def filter_artifacts(
    data: Dict[str, Any],
    memory_type: Optional[MemoryType] = None,
    tags: Optional[List[str]] = None,
    since: Optional[str] = None
) -> bool:
    """Filter artifacts by type, tags, and time.
    
    Returns True if artifact passes all filters.
    """
    # Memory type filtering
    if memory_type:
        artifact_type = MemoryType(data.get("memory_type", MemoryType.FACT.value))
        if artifact_type != memory_type:
            return False
    
    # Tag filtering (AND logic - artifact must have ALL specified tags)
    if tags:
        tag_filter_match = all(tag in data["tags"] for tag in tags)
        if not tag_filter_match:
            return False
    
    # Time-based filtering
    if since:
        since_dt = datetime.fromisoformat(since)
        artifact_dt = datetime.fromisoformat(data["created_at"])
        if artifact_dt < since_dt:
            return False
    
    return True