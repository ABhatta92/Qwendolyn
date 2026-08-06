"""Deterministic execution of planner-selected capability calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qwendolyn.capabilities.base import CapabilityResult
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ExecutionRecord:
    """
    Immutable record of a single capability execution.
    """

    call_id: str
    operation: str
    arguments: dict[str, Any]
    result: CapabilityResult

    @property
    def success(self) -> bool:
        return self.result.success

    def to_dict(self) -> dict[str, Any]:

        return {
            "call_id": self.call_id,
            "operation": self.operation,
            "arguments": self.arguments,
            "success": self.result.success,
            "message": self.result.message,
            "artifacts": self.result.artifacts,
            "metrics": self.result.metrics,
            "data": self.result.data,
            "error": self.result.error,
        }

    def __str__(self) -> str:

        return (
            f"Operation: {self.operation}\n"
            f"Success: {self.result.success}\n"
            f"Message: {self.result.message}\n"
            f"Artifacts: {self.result.artifacts}\n"
            f"Metrics: {self.result.metrics}\n"
            f"Error: {self.result.error}"
        )


class Executor:

    def __init__(
        self,
        registry: Any,
    ) -> None:

        self.registry = registry

    def execute(
        self,
        call: Any,
    ) -> ExecutionRecord:

        logger.info(
            "Executing '%s' (call_id=%s).",
            call.name,
            call.id,
        )

        logger.debug(
            "Arguments: %s",
            call.arguments,
        )

        result = self.registry.execute(
            function_name=call.name,
            **call.arguments,
        )

        if result.success:

            logger.info(
                "Execution succeeded: %s",
                result.message,
            )

        else:

            logger.warning(
                "Execution failed: %s",
                result.message,
            )

        if result.artifacts:

            logger.info(
                "Artifacts: %s",
                result.artifacts,
            )

        if result.metrics:

            logger.info(
                "Metrics: %s",
                result.metrics,
            )

        return ExecutionRecord(
            call_id=call.id,
            operation=call.name,
            arguments=call.arguments,
            result=result,
        )