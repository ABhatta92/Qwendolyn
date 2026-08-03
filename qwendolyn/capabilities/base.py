from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CapabilityResult:
    """
    Standard return type for every capability function.
    """

    success: bool
    message: str

    data: Any | None = None

    artifacts: dict[str, list[str]] = field(
        default_factory=lambda: {
            "files": [],
            "tables": [],
            "views": [],
            "vectors": [],
        }
    )

    metrics: dict[str, Any] = field(
        default_factory=dict
    )

    logs: list[str] = field(
        default_factory=list
    )

    error: dict[str, Any] | None = None


class BaseCapability(ABC):
    """
    Base class for all capabilities exposed to the agent.

    A capability represents a domain (filesystem, python, database, web, etc.)
    and may expose one or more callable functions to the LLM.
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
        Returns every OpenAI/Qwen-compatible function schema exposed
        by this capability.
        """
        ...

    @abstractmethod
    def execute(
        self,
        function_name: str,
        **kwargs: Any,
    ) -> CapabilityResult:
        """
        Execute one of the capability's functions.

        Example
        -------
            execute("read_file", path="hello.txt")
        """
        ...