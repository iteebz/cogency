from .edit import edit
from .find import find
from .list import ls
from .read import read
from .recall import recall
from .replace import replace
from .scrape import scrape
from .search import search
from .shell import shell
from .write import write

code = [read, write, edit, ls, find, replace, shell]
web = [scrape, search]
memory = [recall]
defaults = code + web + memory

__all__ = [
    "code",
    "defaults",
    "edit",
    "find",
    "ls",
    "memory",
    "read",
    "recall",
    "replace",
    "scrape",
    "search",
    "shell",
    "web",
    "write",
]
