from qwendolyn.agent.agent import Agent
from qwendolyn.capabilities.database import DatabaseCapability
from qwendolyn.capabilities.filesystem import FileSystemCapability
from qwendolyn.capabilities.python_tool import PythonCapability
from qwendolyn.capabilities.registry import CapabilityRegistry
from qwendolyn.config import DB, WORKSPACE
from qwendolyn.llm import OllamaLLM
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


def create_agent(
    model_name: str = "qwen3",
    temperature: float = 0.2,
) -> Agent:
    """
    Bootstrap the Qwendolyn agent.
    """

    logger.info("Bootstrapping Qwendolyn (model=%s, temperature=%s).", model_name, temperature)
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
            working_directory=WORKSPACE,
        )
    )

    registry.register(
        DatabaseCapability(
            database=DB / "qwendolyn.duckdb",
        )
    )

    agent = Agent(
        llm=llm,
        registry=registry,
    )
    logger.info("Qwendolyn bootstrap complete (capabilities=%s).", ", ".join(registry.list_capabilities()))
    return agent
