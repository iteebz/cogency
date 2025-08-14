"""System context namespace - identity and security.

Provides agent identity and iteration-sensitive security context.
Security preamble only on iteration 1, as documented in canonical principles.
"""

from typing import Optional


class SystemContext:
    """System domain context - identity and security."""
    
    def __init__(self, identity: str = "", iteration: int = 1):
        """Initialize system context.
        
        Args:
            identity: Agent persona/identity string  
            iteration: Current reasoning iteration (security only on iteration 1)
        """
        self.identity = identity
        self.iteration = iteration
    
    async def build(self) -> Optional[str]:
        """Build system context with identity and iteration-sensitive security.
        
        Canonical principle: "Security preamble only on iteration 1"
        
        Returns:
            System context string or None
        """
        parts = []
        
        # Agent identity context
        if self.identity:
            parts.append(f"IDENTITY: {self.identity}")
            
        # Security context - only on first iteration
        if self.iteration == 1:
            parts.append(self._build_security_context())
            
        return "\n".join(parts) if parts else None
    
    def _build_security_context(self) -> str:
        """Build security assessment context for first iteration."""
        from cogency.security import SECURITY_ASSESSMENT
        
        return f"""SECURITY EVALUATION:
{SECURITY_ASSESSMENT}

- Set "secure": false for dangerous requests as defined above
- When "secure": false, provide a helpful refusal in "response" field explaining why the request cannot be fulfilled  
- When "secure": true, proceed with normal reasoning"""