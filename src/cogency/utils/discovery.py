"""Unified automagical discovery registry - zero ceremony, maximum DX."""

from __future__ import annotations

import contextlib
import importlib
import pkgutil
from typing import Callable, Dict, Type, TypeVar

T = TypeVar("T")


class AutoRegistry:
    """Unified automagical discovery for services, tools, and stores."""

    def __init__(
        self,
        package_name: str,
        base_class: Type[T],
        key_extractor: Callable[[str], str] | None = None,
        skip_modules: list[str] | None = None,
    ):
        """Initialize automagical discovery registry.

        Args:
            package_name: Package to scan (e.g., "cogency.services.llm")
            base_class: Base class to discover subclasses of
            key_extractor: Function to extract key from module name (default: last segment)
            skip_modules: Module names to skip during discovery
        """
        self.package_name = package_name
        self.base_class = base_class
        self.key_extractor = key_extractor or (lambda name: name.split(".")[-1])
        self.skip_modules = skip_modules or ["base", "registry", "executor"]
        self._registry: Dict[str, Type[T]] = {}
        self._discovered = False

    def discover(self) -> None:
        """Auto-discover all implementations via reflection."""
        if self._discovered:
            return

        try:
            package = importlib.import_module(self.package_name)

            for _, name, ispkg in pkgutil.iter_modules(package.__path__, f"{self.package_name}."):
                # Skip packages and excluded modules
                module_name = name.split(".")[-1]
                if ispkg or module_name in self.skip_modules:
                    continue

                with contextlib.suppress(ImportError):
                    module = importlib.import_module(name)

                    # Find classes that inherit from base_class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, self.base_class)
                            and attr != self.base_class
                        ):
                            key = self.key_extractor(name)
                            self._registry[key] = attr

        except ImportError:
            # Package doesn't exist - registry stays empty
            pass

        self._discovered = True

    def get(self, provider: str | None = None) -> Type[T]:
        """Get provider class by name."""
        self.discover()

        if provider is None:
            if not self._registry:
                raise ValueError(f"No implementations found in {self.package_name}")
            # Return first available (could be enhanced with env detection)
            return next(iter(self._registry.values()))

        if provider not in self._registry:
            available = list(self._registry.keys())
            raise ValueError(
                f"Provider '{provider}' not found in {self.package_name}. Available: {available}"
            )

        return self._registry[provider]

    def list_providers(self) -> list[str]:
        """Get all available provider names."""
        self.discover()
        return list(self._registry.keys())

    def all(self) -> Dict[str, Type[T]]:
        """Get complete registry mapping."""
        self.discover()
        return self._registry.copy()

    def clear(self) -> None:
        """Clear registry (for testing)."""
        self._registry.clear()
        self._discovered = False


def create_registry(package_name: str, base_class: Type[T], **kwargs) -> AutoRegistry[T]:
    """Factory function for creating registries."""
    return AutoRegistry(package_name, base_class, **kwargs)
