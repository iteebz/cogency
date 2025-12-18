from collections import defaultdict

from .protocols import Storage, Tool


class ToolRegistry:
    def __init__(self, storage: Storage):
        self.by_category: defaultdict[str, list[Tool]] = defaultdict(list)
        self.by_name: dict[str, Tool] = {}
        self.storage = storage
        self._register_builtins()

    def _register_builtins(self):
        from cogency.tools import (
            Edit,
            Find,
            List,
            Read,
            Recall,
            Replace,
            Scrape,
            Search,
            Shell,
            Write,
        )

        self.register(Read, "code")
        self.register(Write, "code")
        self.register(Edit, "code")
        self.register(List, "code")
        self.register(Find, "code")
        self.register(Replace, "code")
        self.register(Shell, "code")
        self.register(Scrape, "web")
        self.register(Search, "web")
        self.register(Recall, "memory")

    def register(self, tool_instance: Tool, category: str):
        if not hasattr(tool_instance, "name"):
            raise ValueError("Tool instance must have a 'name' attribute.")

        if tool_instance.name in self.by_name:
            raise ValueError(f"Tool with name '{tool_instance.name}' is already registered.")

        self.by_category[category].append(tool_instance)
        self.by_name[tool_instance.name] = tool_instance

    def __call__(self) -> list[Tool]:
        all_tools: list[Tool] = [tool for tools in self.by_category.values() for tool in tools]
        return list(dict.fromkeys(all_tools))

    def category(self, categories: str | list[str]) -> list[Tool]:
        if isinstance(categories, str):
            categories = [categories]

        filtered: set[Tool] = set()
        for category in categories:
            if category in self.by_category:
                for tool in self.by_category[category]:
                    filtered.add(tool)
        return list(filtered)

    def name(self, names: str | list[str]) -> list[Tool]:
        if isinstance(names, str):
            names = [names]

        filtered: set[Tool] = set()
        for name in names:
            if name in self.by_name:
                filtered.add(self.by_name[name])
        return list(filtered)

    def get(self, name: str) -> Tool | None:
        return self.by_name.get(name)
