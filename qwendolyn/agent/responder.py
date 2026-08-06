"""Evidence-bound final user communication."""
from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


class Responder:
    def __init__(self, llm: Any) -> None:
        self.llm = llm

    def respond(self, objective: str, history: list[Any], completed: bool, failure_reason: str | None = None) -> str:
        logger.info("Generating evidence-bound response (completed=%s, result_count=%d).", completed, len(history))
        evidence = [record.to_dict() for record in history]
        message = HumanMessage(content=(
            f"Objective:\n{objective}\n\nVerified capability results:\n{evidence}\n\n"
            f"Task state: {'completed' if completed else 'not completed'}.\n"
            f"Observed failure reason: {failure_reason or 'none'}."
        ))
        response = self.llm.invoke(messages=[message], role="responder")
        logger.info("Evidence-bound response generated.")
        return str(response.content)
