"""Memory preparation utilities."""
from typing import Optional, List

from cogency.memory.core import MemoryBackend, MemoryType


def should_extract_memory(query: str) -> bool:
    """Simple heuristic: extract if query contains insights, novel info, or actionable patterns."""
    extract_indicators = [
        'learn', 'remember', 'important', 'note', 'save', 'store',
        'insight', 'discovered', 'found', 'solution', 'fix', 'solved',
        'pattern', 'trend', 'observation', 'conclusion', 'result'
    ]
    return any(indicator in query.lower() for indicator in extract_indicators)


async def save_extracted_memory(
    memory_summary: Optional[str], 
    memory: MemoryBackend, 
    user_id: str,
    tags: Optional[List[str]] = None,
    memory_type: str = "fact"
) -> None:
    """Save memory summary with LLM-generated tags and memory type."""
    if memory_summary and memory_summary.strip():
        # Convert string memory type to enum
        try:
            memory_type_enum = MemoryType(memory_type)
        except ValueError:
            memory_type_enum = MemoryType.FACT
        
        # Use LLM-generated tags or fallback to basic tag
        final_tags = tags if tags else ["extracted"]
        
        await memory.create(
            memory_summary, 
            memory_type=memory_type_enum,
            tags=final_tags, 
            user_id=user_id
        )