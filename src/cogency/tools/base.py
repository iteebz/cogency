"""Base tool interface."""

from abc import ABC, abstractmethod

from ..lib.result import Result


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
    async def execute(self, **kwargs) -> Result[str, str]:
        """Execute tool with given arguments."""
        pass
