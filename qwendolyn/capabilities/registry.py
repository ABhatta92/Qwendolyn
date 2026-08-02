from typing import Any

from qwendolyn.capabilities.base import BaseCapability
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="app")


class CapabilityRegistry:

    def __init__(self):

        self._capabilities: dict[str, BaseCapability] = {}
        self._function_map: dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability):

        self._capabilities[capability.name] = capability

        for function in capability.functions:

            function_name = function["function"]["name"]

            if function_name in self._function_map:
                raise ValueError(
                    f"Function '{function_name}' is already registered."
                )

            self._function_map[function_name] = capability

        logger.info(
            "Registered capability '%s' with %d functions",
            capability.name,
            len(capability.functions),
        )

    def get_capability(self, name: str) -> BaseCapability:

        if name not in self._capabilities:
            raise ValueError(
                f"Unknown capability '{name}'."
            )

        return self._capabilities[name]

    def get_function(self, function_name: str) -> BaseCapability:

        if function_name not in self._function_map:
            raise ValueError(
                f"Unknown function '{function_name}'."
            )

        return self._function_map[function_name]

    def execute(
        self,
        function_name: str,
        **kwargs: Any,
    ) -> Any:

        capability = self.get_function(function_name)

        logger.info(
            "Executing function '%s' via capability '%s'",
            function_name,
            capability.name,
        )

        return capability.execute(
            function_name=function_name,
            **kwargs,
        )

    def schemas(self) -> list[dict]:

        schemas: list[dict] = []

        for capability in self._capabilities.values():
            schemas.extend(capability.functions)

        return schemas

    def list_capabilities(self) -> dict[str, str]:

        return {
            capability.name: capability.description
            for capability in self._capabilities.values()
        }