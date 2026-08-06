"""Autonomous plan-execute-verify loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qwendolyn.agent.executor import ExecutionRecord, Executor
from qwendolyn.agent.planner import Planner
from qwendolyn.agent.responder import Responder
from qwendolyn.agent.verifier import Verifier
from qwendolyn.llm import OllamaLLM
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class TaskState:
    objective: str
    history: list[ExecutionRecord] = field(default_factory=list)
    completed: bool = False
    failure_reason: str | None = None


class Agent:

    def __init__(
        self,
        registry: Any,
        planner_llm: OllamaLLM | None = None,
        responder_llm: OllamaLLM | None = None,
        max_iterations: int = 24,
    ) -> None:

        self.planner = Planner(
            planner_llm or OllamaLLM(model_name="qwen2.5:1.5b"),
            registry,
        )

        self.executor = Executor(registry)

        self.verifier = Verifier()

        self.responder = Responder(
            responder_llm or OllamaLLM(model_name="qwen3"),
        )

        self.max_iterations = max_iterations

        logger.info(
            "Agent initialized (planner=%s, responder=%s, max_iterations=%d).",
            "qwen2.5:1.5b",
            "qwen3",
            max_iterations,
        )

    def run(
        self,
        prompt: str,
        persona: str | None = None,
    ) -> str:

        del persona

        state = TaskState(
            objective=prompt,
        )

        logger.info(
            "Starting task."
        )

        for iteration in range(1, self.max_iterations + 1):

            logger.info(
                "Iteration %d/%d",
                iteration,
                self.max_iterations,
            )

            plan = self.planner.plan(
                objective=state.objective,
                history=state.history,
            )

            verification = self.verifier.verify(
                objective=state.objective,
                history=state.history,
                planner_calls=len(plan.calls),
            )

            if verification.complete:

                state.completed = True

                logger.info(
                    "Objective verified."
                )

                break

            if not plan.calls:

                state.failure_reason = verification.reason

                logger.warning(
                    "Planner stopped before objective was verified: %s",
                    verification.reason,
                )

                break

            for call in plan.calls:

                record = self.executor.execute(call)

                state.history.append(record)

                if not record.success:

                    state.failure_reason = record.result.message

                    logger.warning(
                        "Execution failed: %s",
                        state.failure_reason,
                    )

                    return self.responder.respond(
                        objective=state.objective,
                        history=state.history,
                        completed=False,
                        failure_reason=state.failure_reason,
                    )

        else:

            state.failure_reason = (
                f"Maximum iteration limit ({self.max_iterations}) reached."
            )

            logger.warning(
                state.failure_reason,
            )

        logger.info(
            "Generating final response."
        )

        return self.responder.respond(
            objective=state.objective,
            history=state.history,
            completed=state.completed,
            failure_reason=state.failure_reason,
        )