"""Storage domain - foundational persistence infrastructure.

Storage is FOUNDATIONAL INFRASTRUCTURE consumed by all domains:
- state/ uses storage for execution context persistence
- knowledge/ uses storage for knowledge artifacts
- user/ uses storage for profile persistence

Storage does NOT belong to any single domain - it's shared infrastructure.
"""

from .sqlite import SQLite
from .store import Store
from .supabase import Supabase

__all__ = ["Store", "SQLite", "Supabase"]
