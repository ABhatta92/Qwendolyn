from abc import ABC, abstractmethod


class BaseTool(ABC):
    """
    Base class for all tools.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, **kwargs):
        """
        Execute the tool.
        """
        pass