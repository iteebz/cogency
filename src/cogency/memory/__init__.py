"""Memory domain - MOVED to context/memory/ namespace.

Backward compatibility imports - implementations moved to context/memory/.
"""

# Backward compatibility imports from consolidated namespace
from cogency.context.memory import Memory, Profile, learn, Recall

__all__ = ["Memory", "Profile", "learn", "Recall"]
