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
    planner_model: str = "qwen2.5:1.5b",
    responder_model: str = "qwen3",
    temperature: float = 0.2,
) -> Agent:
    """
    Bootstrap the Qwendolyn agent.
    """

    logger.info(
        "Bootstrapping Qwendolyn (planner=%s, responder=%s).",
        planner_model,
        responder_model,
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

    planner_llm = OllamaLLM(
        model_name=planner_model,
        temperature=temperature,
    )

    responder_llm = OllamaLLM(
        model_name=responder_model,
        temperature=temperature,
    )

    agent = Agent(
        registry=registry,
        planner_llm=planner_llm,
        responder_llm=responder_llm,
    )

    logger.info(
        "Qwendolyn bootstrap complete (capabilities=%s).",
        ", ".join(registry.list_capabilities()),
    )

    return agent