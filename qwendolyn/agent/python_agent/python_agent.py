from __future__ import annotations

from pathlib import Path

from qwendolyn.agent.agent import Agent
from qwendolyn.agent.planner import Planner
from qwendolyn.agent.python_agent.validator import Validator
from qwendolyn.config import WORKSPACE
from qwendolyn.runtime.python_runner import PythonRunner


class PythonAgent(Agent):

    def __init__(
        self,
        llm,
        planner_llm,
    ):

        runner = PythonRunner(
            working_directory=WORKSPACE,
        )

        planner = Planner(
            llm=planner_llm,
        )

        validator = Validator(
            workspace=WORKSPACE,
        )

        super().__init__(
            llm=llm,
            runner=runner,
            planner=planner,
            validator=validator,
            language="Python",
        )