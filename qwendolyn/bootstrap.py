from qwendolyn.agent import Agent
from qwendolyn.capabilities.filesystem import FileSystemCapability
from qwendolyn.capabilities.python_tool import PythonCapability
from qwendolyn.capabilities.database import DatabaseCapability
from qwendolyn.capabilities.registry import CapabilityRegistry
from qwendolyn.config import FILES, WORKSPACE
from qwendolyn.llm import OllamaLLM


def create_agent(
    model_name: str = "qwen3",
    temperature: float = 0.2,
) -> Agent:
    """
    Creates and wires together the Qwendolyn application.
    """

    llm = OllamaLLM(
        model_name=model_name,
        temperature=temperature,
    )

    registry = CapabilityRegistry()

    registry.register(
        FileSystemCapability(
            workspace=WORKSPACE,
        )
    )

    registry.register(
        PythonCapability(
            working_directory=FILES,
        )
    )

    registry.register(
            DatabaseCapability(
                working_directory=FILES,
            )
        )

    return Agent(
        llm=llm,
        registry=registry,
    )