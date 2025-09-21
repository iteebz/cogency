"""
A simple, beautiful, and self-updating toolkit for all agent tools.
"""

import importlib.util as iu
import inspect
from collections import defaultdict
from pathlib import Path

from ..core.protocols import Tool


class ToolRegistry:
    """
    A callable toolkit that auto-discovers and provides tools.
    """

    def __init__(self, discover: bool = True):
        self.by_category = defaultdict(list)
        self.by_name = {}
        if discover:
            self._discover()

    def _discover(self, root: Path | None = None):
        """Finds and registers all Tool classes from a root directory."""
        if root is None:
            root = Path(__file__).parent

        for path in root.glob("*/*.py"):
            if path.name.startswith("__"):
                continue

            category = path.parent.name
            name = f"cogency.tools.{category}.{path.stem}"

            spec = iu.spec_from_file_location(name, path)
            mod = iu.module_from_spec(spec)
            spec.loader.exec_module(mod)

            for _, cls in inspect.getmembers(mod, inspect.isclass):
                if issubclass(cls, Tool) and cls is not Tool:
                    self.register(cls(), category)

    def register(self, tool_instance: Tool, category: str):
        """Registers a tool instance, indexing it by category and its declared name."""
        if not isinstance(tool_instance, Tool):
            raise TypeError("Tool must be an instance of a Tool subclass.")

        if not hasattr(tool_instance, "name"):
            raise ValueError("Tool instance must have a 'name' attribute.")

        if tool_instance.name in self.by_name:
            raise ValueError(f"Tool with name '{tool_instance.name}' is already registered.")

        self.by_category[category].append(type(tool_instance))
        self.by_name[tool_instance.name] = type(tool_instance)

    def __call__(self) -> list[Tool]:
        """Returns a list of all tool instances in the registry."""
        classes = {c for cat_classes in self.by_category.values() for c in cat_classes}
        return [cls() for cls in classes]

    def category(self, categories: str | list[str]) -> list[Tool]:
        """
        Returns a list of tool instances filtered by category.
        """
        if isinstance(categories, str):
            categories = [categories]

        filtered_classes = set()
        for category in categories:
            if category in self.by_category:
                for cls in self.by_category[category]:
                    filtered_classes.add(cls)
        return [cls() for cls in filtered_classes]

    def name(self, names: str | list[str]) -> list[Tool]:
        """
        Returns a list of tool instances filtered by name.
        """
        if isinstance(names, str):
            names = [names]

        filtered_classes = set()
        for name in names:
            if name in self.by_name:
                filtered_classes.add(self.by_name[name])
        return [cls() for cls in filtered_classes]

    def get(self, name: str) -> Tool | None:
        """Retrieves a tool instance by its name."""
        tool_class = self.by_name.get(name)
        if tool_class:
            return tool_class()
        return None
