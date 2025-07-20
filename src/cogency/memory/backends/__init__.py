"""Auto-discovery for memory backends."""
import importlib
import pkgutil
from typing import Dict, Type, Any
from ..core import MemoryBackend


_BACKEND_REGISTRY: Dict[str, Type[MemoryBackend]] = {}


def _discover_backends():
    """Auto-discover backend classes via filesystem reflection."""
    if _BACKEND_REGISTRY:
        return _BACKEND_REGISTRY
    
    # Scan this package for backend modules
    package = __package__ or __name__
    for _, module_name, _ in pkgutil.iter_modules(__path__, package + "."):
        try:
            module = importlib.import_module(module_name)
            # Look for classes that inherit from MemoryBackend
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, MemoryBackend) and 
                    attr != MemoryBackend and
                    attr_name != "BaseBackend"):  # Skip abstract base class
                    # Register with simplified name (remove "Backend" suffix)
                    name = attr_name.lower().replace("backend", "").replace("memory", "")
                    _BACKEND_REGISTRY[name] = attr
        except ImportError:
            continue
    
    return _BACKEND_REGISTRY


def get_backend(name: str) -> Type[MemoryBackend]:
    """Get backend class by name."""
    backends = _discover_backends()
    if name not in backends:
        available = ", ".join(backends.keys())
        raise ValueError(f"Backend '{name}' not found. Available: {available}")
    return backends[name]


def list_backends() -> list[str]:
    """List available backend names."""
    return list(_discover_backends().keys())