"""Generic registry pattern for service management with singleton pattern."""

from typing import Callable, Dict, Optional, Type, TypeVar, Union

T = TypeVar("T")


class Provider:
    """Manages providers with auto-detection, singletons, and lazy initialization."""

    def __init__(
        self,
        providers: Union[Dict[str, Type[T]], Callable[[], Dict[str, Type[T]]]],
        detect_fn: Optional[Callable[[], str]] = None,
        default: Optional[str] = None,
    ):
        self._providers_source = providers
        self._providers_cache = None
        self.detect_fn = detect_fn
        self.default = default
        self._instances: Dict[str, T] = {}

    @property
    def providers(self) -> Dict[str, Type[T]]:
        """Get providers dict, loading lazily if needed."""
        if self._providers_cache is None:
            if callable(self._providers_source):
                self._providers_cache = self._providers_source()
            else:
                self._providers_cache = self._providers_source
        return self._providers_cache

    def get(self, provider: Optional[str] = None) -> Type[T]:
        """Get provider class (not instance)."""
        if provider is None:
            if self.detect_fn:
                provider = self.detect_fn()
            elif self.default:
                provider = self.default
            else:
                raise ValueError("No provider specified and no default/detection available")

        if provider not in self.providers:
            available = ", ".join(self.providers.keys())
            raise ValueError(f"Provider '{provider}' not found. Available: {available}")

        return self.providers[provider]

    def instance(self, provider: Optional[str] = None, **kwargs) -> T:
        """Get singleton instance of provider."""
        if provider is None:
            if self.detect_fn:
                provider = self.detect_fn()
            elif self.default:
                provider = self.default
            else:
                raise ValueError("No provider specified and no default/detection available")

        if provider not in self.providers:
            available = ", ".join(self.providers.keys())
            raise ValueError(f"Provider '{provider}' not found. Available: {available}")

        cache_key = f"{provider}:{hash(frozenset(kwargs.items()))}"

        if cache_key not in self._instances:
            provider_class = self.providers[provider]
            self._instances[cache_key] = provider_class(**kwargs)

        return self._instances[cache_key]

    def all_classes(self) -> Dict[str, Type[T]]:
        """Get all provider classes for export."""
        return self.providers.copy()
