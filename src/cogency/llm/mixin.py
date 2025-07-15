from abc import abstractmethod
from typing import Dict, List


class ProviderMixin:
    """Shared provider functionality with MAGICAL key rotation."""
    
    def _rotate_client(self):
        """MAGICAL key rotation on every invoke."""
        if self.key_rotator:
            self._init_client()
    
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