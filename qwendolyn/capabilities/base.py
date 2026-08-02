from abc import ABC, abstractmethod


class BaseCapability(ABC):
    """
    Base class for every tool exposed to the LLM.
    """

    def __init__(
        self,
        name: str,
        description: str,
    ):
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        JSON Schema describing the capability arguments.
        """
        pass

    @property
    def schema(self) -> dict:
        """
        OpenAI/Qwen compatible tool schema.
        """

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    def run(self, **kwargs):
        """
        Execute the capability.
        """
        pass