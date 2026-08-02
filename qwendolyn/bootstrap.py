from qwendolyn.config import FILES, WORKSPACE

from qwendolyn.agent import Agent
from qwendolyn.llm import OllamaLLM
from qwendolyn.capabilities.registry import CapabilityRegistry
from qwendolyn.capabilities.filesystem import FileSystemCapability
from qwendolyn.capabilities.python_tool import PythonCapability


def create_agent():

    llm = OllamaLLM()

    registry = CapabilityRegistry()

    registry.register(
        FileSystemCapability(WORKSPACE)
    )

    registry.register(
        PythonCapability(FILES)
    )

    return Agent(
        llm=llm,
        registry=registry,
    )