"""Shared contracts for Qwendolyn capabilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


ArtifactMap = dict[str, list[str]]


def empty_artifacts() -> ArtifactMap:
    return {"files": [], "tables": [], "views": [], "vectors": []}


@dataclass(slots=True)
class CapabilityError:
    type: str
    message: str
    traceback: str | None = None


@dataclass(slots=True)
class CapabilityResult:
    """The only result shape returned by every capability operation."""

    success: bool
    message: str
    data: Any | None = None
    artifacts: ArtifactMap = field(default_factory=empty_artifacts)
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    error: CapabilityError | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe, stable representation for the planner and responder."""
        return asdict(self)


class BaseCapability(ABC):
    """A cohesive external-system boundary exposed as LLM-callable operations."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def functions(self) -> list[dict[str, Any]]:
        """OpenAI-compatible function schemas for this capability."""

    @abstractmethod
    def execute(self, function_name: str, **kwargs: Any) -> CapabilityResult:
        """Execute one operation and always return ``CapabilityResult``."""
