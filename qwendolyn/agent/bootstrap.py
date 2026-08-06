from pathlib import Path

from qwendolyn.agent.agent import Agent
from qwendolyn.llm.llm import LLM
from qwendolyn.runtime.frontend_runner import FrontendRunner
from qwendolyn.runtime.python_runner import PythonRunner
from qwendolyn.config import WORKSPACE

PROMPTS = (
    Path(__file__).resolve().parent.parent
    / "llm"
    / "prompts"
)


def create_python_agent() -> Agent:

    llm = LLM(
        model_name="qwen3",
        temperature=0.1,
        system_prompt=PROMPTS / "python.txt",
    )

    return Agent(
        llm=llm,
        runner=PythonRunner(working_directory=WORKSPACE),
        language="Python",
    )


def create_frontend_agent() -> Agent:

    llm = LLM(
        model_name="qwen3",
        temperature=0.3,
        system_prompt=PROMPTS / "frontend.txt",
    )

    return Agent(
        llm=llm,
        runner=FrontendRunner(working_directory=WORKSPACE),
        language="Frontend",
    )


def create_agents() -> dict[str, Agent]:

    return {
        "Python": create_python_agent(),
        "Frontend": create_frontend_agent(),
    }