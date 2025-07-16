"""Memory preparation utilities."""
from typing import Optional

from cogency.memory.base import BaseMemory


def should_extract_memory(query: str) -> bool:
    """Simple heuristic: extract if query contains insights, novel info, or actionable patterns."""
    extract_indicators = [
        'learn', 'remember', 'important', 'note', 'save', 'store',
        'insight', 'discovered', 'found', 'solution', 'fix', 'solved',
        'pattern', 'trend', 'observation', 'conclusion', 'result'
    ]
    return any(indicator in query.lower() for indicator in extract_indicators)


async def save_extracted_memory(memory_summary: Optional[str], memory: BaseMemory, user_id: str) -> None:
    """Save memory summary only if not null or empty."""
    # TODO: Could make save_memory semantic update in the future
    if memory_summary and memory_summary.strip() and hasattr(memory, 'memorize'):
        await memory.memorize(memory_summary, tags=["insight"], user_id=user_id)