import contextlib
import importlib
from pathlib import Path
from typing import Any, Dict

from cogency.tools.base import BaseTool
from cogency.tools.registry import get_tools, build_registry

# Auto-discover tools by importing all tool modules and collect exported classes
_tools_dir = Path(__file__).parent
_exported_classes: Dict[str, Any] = {}

for tool_file in _tools_dir.glob("*.py"):
    if tool_file.name not in ["__init__.py", "base.py", "registry.py", "executor.py"]:
        module_name = f"cogency.tools.{tool_file.stem}"
        with contextlib.suppress(ImportError):
            module = importlib.import_module(module_name)
            # Export tool classes that are decorated with @tool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseTool) and attr is not BaseTool:
                    _exported_classes[attr_name] = attr

# Make tool classes available for direct import
globals().update(_exported_classes)

__all__ = ["BaseTool", "get_tools", "build_registry"] + list(_exported_classes.keys())
