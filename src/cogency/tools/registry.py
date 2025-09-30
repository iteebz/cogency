from collections import defaultdict

from ..core.protocols import Tool


class ToolRegistry:
    def __init__(self):
        self.by_category = defaultdict(list)
        self.by_name = {}
        self._register_builtins()

    def _register_builtins(self):
        from .file import FileEdit, FileList, FileRead, FileSearch, FileWrite
        from .memory import MemoryRecall
        from .system import SystemShell
        from .web import WebScrape, WebSearch

        self.register(FileRead(), "file")
        self.register(FileWrite(), "file")
        self.register(FileEdit(), "file")
        self.register(FileList(), "file")
        self.register(FileSearch(), "file")
        self.register(SystemShell(), "system")
        self.register(WebScrape(), "web")
        self.register(WebSearch(), "web")
        self.register(MemoryRecall(), "memory")

    def register(self, tool_instance: Tool, category: str):
        if not isinstance(tool_instance, Tool):
            raise TypeError("Tool must be an instance of a Tool subclass.")

        if not hasattr(tool_instance, "name"):
            raise ValueError("Tool instance must have a 'name' attribute.")

        if tool_instance.name in self.by_name:
            raise ValueError(f"Tool with name '{tool_instance.name}' is already registered.")

        self.by_category[category].append(type(tool_instance))
        self.by_name[tool_instance.name] = type(tool_instance)

    def __call__(self) -> list[Tool]:
        classes = {c for cat_classes in self.by_category.values() for c in cat_classes}
        return [cls() for cls in classes]

    def category(self, categories: str | list[str]) -> list[Tool]:
        if isinstance(categories, str):
            categories = [categories]

        filtered_classes = set()
        for category in categories:
            if category in self.by_category:
                for cls in self.by_category[category]:
                    filtered_classes.add(cls)
        return [cls() for cls in filtered_classes]

    def name(self, names: str | list[str]) -> list[Tool]:
        if isinstance(names, str):
            names = [names]

        filtered_classes = set()
        for name in names:
            if name in self.by_name:
                filtered_classes.add(self.by_name[name])
        return [cls() for cls in filtered_classes]

    def get(self, name: str) -> Tool | None:
        tool_class = self.by_name.get(name)
        if tool_class:
            return tool_class()
        return None
