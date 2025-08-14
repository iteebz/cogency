"""Storage domain - foundational persistence infrastructure.

Storage is FOUNDATIONAL INFRASTRUCTURE consumed by all domains:
- state/ uses storage for execution context persistence
- knowledge/ uses storage for knowledge artifacts
- user/ uses storage for profile persistence

Storage does NOT belong to any single domain - it's shared infrastructure.

ARCHITECTURAL CHANGE: SQLite god-object eliminated. Use functional operations:
from cogency.storage.sqlite.profiles import save_profile
from cogency.storage.sqlite.conversations import create_conversation
"""

# Re-export SQLite functional operations for convenience
from . import sqlite
from .store import Store
from .supabase import Supabase

__all__ = ["Store", "Supabase", "sqlite"]
