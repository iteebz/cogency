"""Services - auto-discovery for LLM, embed, and memory backends."""

import importlib
import pkgutil
from typing import Dict, Optional, Type

from .embed.base import BaseEmbed
from .llm.base import BaseLLM


class ServiceRegistry:
    """Auto-discovery registry for services."""

    def __init__(self):
        self._llm_providers: Dict[str, Type[BaseLLM]] = {}
        self._embed_providers: Dict[str, Type[BaseEmbed]] = {}
        self._discovered = False

    def _discover_services(self):
        """Auto-discover all service implementations."""
        if self._discovered:
            return

        # Discover LLM providers
        self._discover_package("cogency.services.llm", BaseLLM, self._llm_providers)

        # Discover embed providers
        self._discover_package("cogency.services.embed", BaseEmbed, self._embed_providers)

        self._discovered = True

    def _discover_package(self, package_name: str, base_class: Type, registry: Dict[str, Type]):
        """Discover implementations in a package."""
        try:
            package = importlib.import_module(package_name)

            for _, name, ispkg in pkgutil.iter_modules(package.__path__, f"{package_name}."):
                if ispkg or name.endswith(".base"):
                    continue

                try:
                    module = importlib.import_module(name)

                    # Find classes that inherit from base_class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, base_class)
                            and attr != base_class
                        ):
                            # Use module name as key (e.g., "openai", "anthropic")
                            key = name.split(".")[-1]
                            registry[key] = attr

                except ImportError:
                    continue

        except ImportError:
            pass

    def get_llm(self, provider: Optional[str] = None) -> Type[BaseLLM]:
        """Get LLM provider class."""
        self._discover_services()

        if provider is None:
            # Auto-detect based on environment
            from cogency.services.llm import detect_llm

            return detect_llm()

        if provider not in self._llm_providers:
            available = list(self._llm_providers.keys())
            raise ValueError(f"LLM provider '{provider}' not found. Available: {available}")

        return self._llm_providers[provider]

    def get_embed(self, provider: Optional[str] = None) -> Type[BaseEmbed]:
        """Get embed provider class."""
        self._discover_services()

        if provider is None:
            provider = "openai"  # Default

        if provider not in self._embed_providers:
            available = list(self._embed_providers.keys())
            raise ValueError(f"Embed provider '{provider}' not found. Available: {available}")

        return self._embed_providers[provider]


# Global registry instance
_registry = ServiceRegistry()

# PURE CLEAN API - zero ceremony
llm = _registry.get_llm
embed = _registry.get_embed

__all__ = ["llm", "embed"]
