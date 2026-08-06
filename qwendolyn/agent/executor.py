"""Deterministic execution of planner-selected capability calls."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qwendolyn.capabilities.base import CapabilityResult
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ExecutionRecord:
    call_id: str
    operation: str
    arguments: dict[str, Any]
    result: CapabilityResult

    def to_dict(self) -> dict[str, Any]:
        return {"call_id": self.call_id, "operation": self.operation, "arguments": self.arguments, "result": self.result.to_dict()}


class Executor:
    def __init__(self, registry: Any) -> None:
        self.registry = registry

    def execute(self, call: Any) -> ExecutionRecord:
        logger.info("Executing operation '%s' (call_id=%s, argument_keys=%s).", call.name, call.id, sorted(call.arguments))
        result = self.registry.execute(call.name, **call.arguments)
        log_method = logger.info if result.success else logger.warning
        log_method("Operation '%s' finished (success=%s, message=%s).", call.name, result.success, result.message)
        return ExecutionRecord(call.id, call.name, call.arguments, result)
