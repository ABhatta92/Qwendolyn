"""Deterministic verification of task completion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class VerificationResult:
    complete: bool
    reason: str


class Verifier:

    def verify(
        self,
        objective: str,
        history: list[Any],
        planner_calls: int,
    ) -> VerificationResult:
        """
        Verify whether the task is complete using only capability evidence.

        Rules
        -----
        1. If the planner requested another capability, the task is not complete.
        2. If any execution failed, the task is not complete.
        3. If no work has been performed, the task is not complete.
        4. Otherwise the task is considered complete.
        """

        logger.info(
            "Verifying task (planner_calls=%d, executions=%d).",
            planner_calls,
            len(history),
        )

        if planner_calls > 0:

            return VerificationResult(
                complete=False,
                reason="Planner requested additional capability execution.",
            )

        if not history:

            return VerificationResult(
                complete=False,
                reason="No capability executions were performed.",
            )

        failed = [
            record
            for record in history
            if not record.result.success
        ]

        if failed:

            last = failed[-1]

            return VerificationResult(
                complete=False,
                reason=(
                    f"Capability '{last.operation}' failed: "
                    f"{last.result.message}"
                ),
            )

        logger.info(
            "Task verified successfully."
        )

        return VerificationResult(
            complete=True,
            reason="Planner has no further actions and all capability executions succeeded.",
        )