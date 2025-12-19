from .edit import Edit
from .find import Find
from .list import List
from .read import Read
from .recall import Recall
from .replace import Replace
from .scrape import Scrape
from .search import Search
from .shell import Shell
from .write import Write

_tools_instance = None


def tools():
    global _tools_instance
    if _tools_instance is None:
        from cogency.core.registry import ToolRegistry
        from cogency.lib.sqlite import default_storage

        _tools_instance = ToolRegistry(default_storage())
    return _tools_instance()


__all__ = [
    "Edit",
    "Find",
    "List",
    "Read",
    "Recall",
    "Replace",
    "Scrape",
    "Search",
    "Shell",
    "Write",
    "tools",
]
