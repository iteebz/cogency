"""Base tool interface."""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Tool interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for agent reference."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for agent understanding."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute tool with given arguments."""
        pass
