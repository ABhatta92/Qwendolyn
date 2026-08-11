from pathlib import Path

from qwendolyn.agent.agent import Agent
from qwendolyn.agent.planner import Planner
from qwendolyn.agent.python_agent.validator import Validator
from qwendolyn.config import WORKSPACE, AGENT_ROOT, QWENDOLYN_ROOT
from qwendolyn.llm.llm import LLM
from qwendolyn.runtime.python_runner import PythonRunner


PYTHON_PROMPT = AGENT_ROOT / "python_agent" / "prompt.txt"
PLANNER_PROMPT = QWENDOLYN_ROOT / "llm" / "prompts" / "planner.txt"


def create_python_agent() -> Agent:

    worker_llm = LLM(
        model_name="qwen3",
        temperature=0.1,
        system_prompt=PYTHON_PROMPT,
    )

    planner_llm = LLM(
        model_name="qwen3",
        temperature=0.1,
        system_prompt=PLANNER_PROMPT,
    )

    runner = PythonRunner(
        working_directory=WORKSPACE,
    )

    planner = Planner(
        llm=planner_llm,
    )

    validator = Validator(
        workspace=WORKSPACE,
    )

    return Agent(
        llm=worker_llm,
        runner=runner,
        planner=planner,
        validator=validator,
        language="Python",
    )


def create_agents() -> dict[str, Agent]:

    return {
        "Python": create_python_agent(),
    }