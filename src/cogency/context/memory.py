"""Memory context namespace - user profile injection.

Memory domain lives separate from state - gets injected during context assembly.
Preserves memory.activate() functionality exactly as documented.
"""

from typing import Optional, Any


class MemoryContext:
    """Memory domain context - profile injection first."""
    
    def __init__(self, memory: Any, user_id: str):
        """Initialize memory context.
        
        Args:
            memory: Memory component instance
            user_id: User identifier for profile retrieval
        """
        self.memory = memory
        self.user_id = user_id
    
    async def build(self) -> Optional[str]:
        """Build memory context using memory.activate() pattern.
        
        Preserves exact functionality from Agent.run():
        memory_context = await memory.activate(user_id)
        
        Returns:
            Profile context string or None
        """
        if not self.memory:
            return None
            
        try:
            # Canonical memory activation pattern - preserved exactly
            profile_context = await self.memory.activate(self.user_id)
            return profile_context if profile_context else None
            
        except Exception as e:
            from cogency.events import emit
            emit("context", namespace="memory", status="error", error=str(e))
            return None