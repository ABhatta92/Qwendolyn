from qwendolyn.agent.agent import Agent
from qwendolyn.runtime.python_runner import PythonRunner
from qwendolyn.config import WORKSPACE

class PythonAgent(Agent):

    def __init__(self, llm):

        super().__init__(
            llm=llm,
            runner=PythonRunner(working_directory=WORKSPACE),
            language="Python",
        )