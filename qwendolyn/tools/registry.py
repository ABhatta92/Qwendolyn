from qwendolyn.tools.base import BaseTool


class ToolRegistry:

    def __init__(self):

        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):

        self._tools[tool.name] = tool

    def get(self, name: str):

        if name not in self._tools:
            raise ValueError(f"Unknown tool '{name}'")

        return self._tools[name]

    def run(self, name: str, **kwargs):

        return self.get(name).run(**kwargs)

    def list_tools(self):

        return {
            name: tool.description
            for name, tool in self._tools.items()
        }