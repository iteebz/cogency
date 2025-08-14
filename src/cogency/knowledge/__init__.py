"""Knowledge domain - MOVED to context/knowledge/ subdomain.

Backward compatibility imports - implementations moved to context/knowledge/.
"""

# Backward compatibility imports from consolidated subdomain
from cogency.context.knowledge import extract, Retrieve, KnowledgeArtifact

__all__ = ["extract", "Retrieve", "KnowledgeArtifact"]
