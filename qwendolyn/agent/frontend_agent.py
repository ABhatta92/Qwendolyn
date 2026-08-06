from qwendolyn.agent.agent import Agent
from qwendolyn.runtime.frontend_runner import FrontendRunner
from qwendolyn.config import WORKSPACE

class FrontendAgent(Agent):

    def __init__(self, llm):

        super().__init__(
            llm=llm,
            runner=FrontendRunner(working_directory=WORKSPACE),
            language="Frontend",
        )