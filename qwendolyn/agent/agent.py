"""Autonomous plan-execute-verify loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qwendolyn.agent.executor import ExecutionRecord, Executor
from qwendolyn.agent.planner import Planner
from qwendolyn.agent.responder import Responder
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class TaskState:
    objective: str
    history: list[ExecutionRecord] = field(default_factory=list)
    completed: bool = False
    failure_reason: str | None = None


class Agent:
    def __init__(self, llm: Any, registry: Any, max_iterations: int = 24) -> None:
        self.planner = Planner(llm, registry)
        self.executor = Executor(registry)
        self.responder = Responder(llm)
        self.max_iterations = max_iterations
        logger.info("Agent initialized (max_iterations=%d).", max_iterations)

    def run(self, prompt: str, persona: str | None = None) -> str:
        """Perform work until verified completion, a capability failure, or the safety limit."""
        del persona  # Personas are intentionally replaced by separate planner/responder prompts.
        state = TaskState(objective=prompt)
        logger.info("Task started (objective_length=%d).", len(prompt))
        for iteration in range(1, self.max_iterations + 1):
            logger.info("Planning iteration %d/%d (prior_results=%d).", iteration, self.max_iterations, len(state.history))
            plan = self.planner.plan(state.objective, state.history)
            if plan.complete:
                # No capability result is interpreted as success; completion requires evidence.
                state.completed = bool(state.history) and all(record.result.success for record in state.history)
                if not state.completed:
                    state.failure_reason = "Planner stopped without sufficient successful capability evidence."
                    logger.warning("Task stopped without verified completion: %s", state.failure_reason)
                else:
                    logger.info("Task completed with %d verified capability result(s).", len(state.history))
                break
            for call in plan.calls:
                record = self.executor.execute(call)
                state.history.append(record)
                if not record.result.success:
                    state.failure_reason = record.result.message
                    logger.warning("Task failed at operation '%s': %s", call.name, state.failure_reason)
                    return self.responder.respond(state.objective, state.history, completed=False, failure_reason=state.failure_reason)
        else:
            state.failure_reason = f"Stopped after {self.max_iterations} planning iterations."
            logger.warning("Task reached iteration limit: %s", state.failure_reason)
        logger.info("Generating final response (completed=%s, results=%d).", state.completed, len(state.history))
        return self.responder.respond(state.objective, state.history, state.completed, state.failure_reason)
