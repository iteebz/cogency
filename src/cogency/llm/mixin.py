from abc import abstractmethod
from typing import Dict, List


class ProviderMixin:
    """Shared provider functionality."""
    
    def _ensure_client(self):
        """Rotate key and reinit client if rotator configured."""
        if self.key_rotator:
            self._init_client()
        
        if not self._get_client():
            name = self.__class__.__name__.replace('LLM', '')
            raise RuntimeError(f"{name} client not initialized.")
    
    def _convert_msgs(self, msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert to provider format."""
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
    
    @abstractmethod
    def _init_client(self):
        """Init provider client."""
        pass
    
    @abstractmethod
    def _get_client(self):
        """Get client instance."""
        pass