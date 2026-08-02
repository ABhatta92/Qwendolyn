from qwendolyn.capabilities.base import BaseCapability
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="app")


class CapabilityRegistry:

    def __init__(self):

        self._tools: dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability):

        self._tools[capability.name] = capability
        logger.info("Registered capability %s", capability.name)

    def get(self, name: str):

        if name not in self._tools:
            raise ValueError(f"Unknown tool '{name}'")

        return self._tools[name]

    def run(self, name: str, **kwargs):

        logger.info("Running capability %s", name)
        return self.get(name).run(**kwargs)

    def list_tools(self):

        return {
            name: tool.description
            for name, tool in self._tools.items()
        }