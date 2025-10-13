from collections import defaultdict

from ..core.protocols import Tool
from ..lib.storage import Storage


class ToolRegistry:
    def __init__(self, storage: Storage):
        self.by_category = defaultdict(list)
        self.by_name = {}
        self.storage = storage
        self._register_builtins()

    def _register_builtins(self):
        from .code.edit import Edit
        from .code.grep import Grep
        from .code.ls import Ls
        from .code.read import Read
        from .code.shell import Shell
        from .code.write import Write
        from .memory.recall import Recall
        from .web.scrape import Scrape
        from .web.search import Search

        self.register(Read(), "code")
        self.register(Write(), "code")
        self.register(Edit(), "code")
        self.register(Ls(), "code")
        self.register(Grep(), "code")
        self.register(Shell(), "code")
        self.register(Scrape(), "web")
        self.register(Search(), "web")
        self.register(Recall(storage=self.storage), "memory")

    def register(self, tool_instance: Tool, category: str):
        if not isinstance(tool_instance, Tool):
            raise TypeError("Tool must be an instance of a Tool subclass.")

        if not hasattr(tool_instance, "name"):
            raise ValueError("Tool instance must have a 'name' attribute.")

        if tool_instance.name in self.by_name:
            raise ValueError(f"Tool with name '{tool_instance.name}' is already registered.")

        self.by_category[category].append(tool_instance)
        self.by_name[tool_instance.name] = tool_instance

    def __call__(self) -> list[Tool]:
        seen = set()
        return [
            cls
            for cat_classes in self.by_category.values()
            for cls in cat_classes
            if not (cls in seen or seen.add(cls))
        ]

    def category(self, categories: str | list[str]) -> list[Tool]:
        if isinstance(categories, str):
            categories = [categories]

        filtered_classes = set()
        for category in categories:
            if category in self.by_category:
                for cls in self.by_category[category]:
                    filtered_classes.add(cls)
        return list(filtered_classes)

    def name(self, names: str | list[str]) -> list[Tool]:
        if isinstance(names, str):
            names = [names]

        filtered_classes = set()
        for name in names:
            if name in self.by_name:
                filtered_classes.add(self.by_name[name])
        return list(filtered_classes)

    def get(self, name: str) -> Tool | None:
        tool_class = self.by_name.get(name)
        if tool_class:
            return tool_class
        return None
