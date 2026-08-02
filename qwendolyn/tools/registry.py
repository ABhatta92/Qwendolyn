from qwendolyn.tools.base import BaseTool
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="app")


class ToolRegistry:

    def __init__(self):

        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):

        self._tools[tool.name] = tool
        logger.info("Registered tool %s", tool.name)

    def get(self, name: str):

        if name not in self._tools:
            raise ValueError(f"Unknown tool '{name}'")

        return self._tools[name]

    def run(self, name: str, **kwargs):

        logger.info("Running tool %s", name)
        return self.get(name).run(**kwargs)

    def list_tools(self):

        return {
            name: tool.description
            for name, tool in self._tools.items()
        }