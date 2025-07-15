from abc import abstractmethod


class EmbedMixin:
    """Shared embedding functionality with MAGICAL key rotation."""
    
    def _rotate_client(self):
        """MAGICAL key rotation on every embed."""
        if self.key_rotator:
            self._init_client()
    
    @abstractmethod
    def _init_client(self):
        """Init provider client."""
        pass
    
    @abstractmethod
    def _get_client(self):
        """Get client instance."""
        pass