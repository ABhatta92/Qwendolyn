from qwendolyn.config import FILES, WORKSPACE

from qwendolyn.llm import OllamaLLM
from qwendolyn.agent import Agent

from qwendolyn.tools.registry import ToolRegistry
from qwendolyn.tools.filesystem import FileSystemTool
from qwendolyn.tools.python_tool import PythonTool


def create_agent():

    llm = OllamaLLM()

    registry = ToolRegistry()

    registry.register(
        FileSystemTool(WORKSPACE)
    )

    registry.register(
        PythonTool(FILES)
    )

    return Agent(
        llm=llm,
        registry=registry,
    )