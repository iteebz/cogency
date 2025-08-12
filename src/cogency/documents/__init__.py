"""Document search domain."""

from .index import index, index_dir, load
from .search import search

__all__ = ["search", "index", "index_dir", "load"]
