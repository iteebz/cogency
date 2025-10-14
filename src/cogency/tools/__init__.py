from ..lib.sqlite import default_storage
from .code.edit import Edit
from .code.grep import Grep
from .code.ls import Ls
from .code.read import Read
from .code.shell import Shell
from .code.write import Write
from .memory.recall import Recall
from .registry import ToolRegistry
from .web.scrape import Scrape
from .web.search import Search

storage = default_storage()
tools = ToolRegistry(storage)

__all__ = [
    "Write",
    "Grep",
    "Read",
    "Edit",
    "Shell",
    "Ls",
    "Scrape",
    "Search",
    "Recall",
    "tools",
]
