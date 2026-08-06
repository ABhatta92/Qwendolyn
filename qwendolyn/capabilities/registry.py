"""Capability registration and deterministic dispatch."""
from __future__ import annotations

import traceback
from typing import Any

from qwendolyn.capabilities.base import BaseCapability, CapabilityError, CapabilityResult
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, BaseCapability] = {}
        self._functions: dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"Capability '{capability.name}' is already registered.")
        for schema in capability.functions:
            name = schema["function"]["name"]
            if name in self._functions:
                raise ValueError(f"Function '{name}' is already registered.")
            self._functions[name] = capability
        self._capabilities[capability.name] = capability
        logger.info("Registered capability '%s' (%d operation(s)).", capability.name, len(capability.functions))

    def execute(self, function_name: str, **kwargs: Any) -> CapabilityResult:
        try:
            capability = self._functions[function_name]
        except KeyError:
            logger.warning("Attempted unknown capability operation '%s'.", function_name)
            return CapabilityResult(False, "Unknown capability operation.", error=CapabilityError("UnknownOperation", f"Unknown operation '{function_name}'."))
        try:
            logger.info("Dispatching operation '%s' to capability '%s'.", function_name, capability.name)
            return capability.execute(function_name, **kwargs)
        except Exception as exc:  # Defensive boundary: callers always receive the contract.
            logger.exception("Unhandled capability exception for '%s'.", function_name)
            return CapabilityResult(False, "Capability execution failed.", error=CapabilityError(type(exc).__name__, str(exc), traceback.format_exc()))

    def schemas(self) -> list[dict[str, Any]]:
        return [schema for capability in self._capabilities.values() for schema in capability.functions]

    def list_capabilities(self) -> dict[str, str]:
        return {name: capability.description for name, capability in self._capabilities.items()}
