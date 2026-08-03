from qwendolyn.agent.executor import Executor
from qwendolyn.agent.planner import Planner
from qwendolyn.agent.responder import Responder
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="agent")


class Agent:

    def __init__(
        self,
        llm,
        registry,
    ):

        self.planner = Planner(
            llm=llm,
            registry=registry,
        )

        self.executor = Executor(
            registry=registry,
        )

        self.responder = Responder(
            llm=llm,
        )

    def run(
        self,
        prompt: str,
        persona: str = "developer",
    ) -> str:

        logger.info("Starting task.")

        context = {
            "prompt": prompt,
            "persona": persona,
            "results": [],
        }

        while True:

            plan = self.planner.plan(context)

            if plan["complete"]:

                logger.info("Planner marked task as complete.")
                break

            execution = self.executor.execute(plan)

            context["results"].append(execution)

        logger.info("Generating final response.")

        return self.responder.respond(context)