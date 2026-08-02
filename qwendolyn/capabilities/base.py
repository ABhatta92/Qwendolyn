from abc import ABC, abstractmethod
from typing import Any


class BaseCapability(ABC):
    """
    Base class for all capabilities exposed to the agent.

    A capability represents a domain (filesystem, python, git, sql, etc.)
    and can expose one or more callable functions to the LLM.
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
    def functions(self) -> list[dict]:
        """
        Returns all OpenAI/Qwen-compatible function definitions
        exposed by this capability.

        Example:

        [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    ...
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    ...
                }
            }
        ]
        """
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        function_name: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute one of the capability's functions.

        Example

            execute("read_file", path="hello.txt")
        """
        raise NotImplementedError